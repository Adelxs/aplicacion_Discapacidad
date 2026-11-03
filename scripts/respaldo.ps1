# Respaldo de la base de datos y del volumen privado de documentos.
#
# Uso:
#   .\scripts\respaldo.ps1
#   .\scripts\respaldo.ps1 -Verificar
#
# -Verificar restaura el respaldo en una base temporal, compara los conteos de
# las tablas y verifica los documentos en un directorio temporal. La base
# temporal se elimina al terminar. No modifica la base ni el volumen reales.

[CmdletBinding()]
param(
    [string]$Destino = "",
    [switch]$Verificar
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not $Destino) {
    $Destino = Join-Path $PSScriptRoot "..\respaldos"
}

$Raiz = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Marca = Get-Date -Format "yyyyMMdd_HHmmss"
$BaseDestino = Join-Path $Destino "base_$Marca.dump"
$DocsDestino = Join-Path $Destino "documentos_$Marca.tar.gz"
$Manifiesto = Join-Path $Destino "respaldo_$Marca.txt"
$ArchivoSql = Join-Path $Destino ".conteos_$Marca.sql"
$BaseTemporal = "citas_municipales_verif_$Marca"
$ConsultaConteos = "SELECT (SELECT count(*) FROM usuarios) || ',' || (SELECT count(*) FROM profesionales) || ',' || (SELECT count(*) FROM pacientes) || ',' || (SELECT count(*) FROM citas) || ',' || (SELECT count(*) FROM atenciones) || ',' || (SELECT count(*) FROM documentos) || ',' || (SELECT count(*) FROM alembic_version)"

function Exec-Docker {
    param([string[]]$Argumentos)

    $preferenciaAnterior = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        $salida = & docker @Argumentos 2>&1
        $codigo = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $preferenciaAnterior
    }

    if ($codigo -ne 0) {
        $texto = (($salida | ForEach-Object { "$_" }) -join "`n").Trim()
        throw "El comando 'docker $($Argumentos -join ' ')' fallo:`n$texto"
    }
    return (($salida | ForEach-Object { "$_" }) -join "`n").Trim()
}

function Contar-Documentos {
    param([string]$Ruta)

    $salida = Exec-Docker @(
        "compose", "exec", "-T", "backend", "sh", "-c",
        "find `"$Ruta`" -type f | wc -l"
    )
    return [int]($salida.Trim())
}

function Hash-Documentos {
    param([string]$Ruta)

    return Exec-Docker @(
        "compose", "exec", "-T", "backend", "sh", "-c",
        "find `"$Ruta`" -type f -exec sha256sum {} + | awk '{print `$1}' | sort | sha256sum"
    )
}

Push-Location $Raiz
try {
    New-Item -ItemType Directory -Force -Path $Destino | Out-Null

    Write-Host "Respaldando base de datos..."
    Exec-Docker @(
        "compose", "exec", "-T", "db", "sh", "-c",
        'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc -f /tmp/diss_respaldo.dump'
    ) | Out-Null
    Exec-Docker @("compose", "cp", "db:/tmp/diss_respaldo.dump", $BaseDestino) | Out-Null
    Exec-Docker @("compose", "exec", "-T", "db", "rm", "-f", "/tmp/diss_respaldo.dump") | Out-Null

    Write-Host "Respaldando documentos..."
    Exec-Docker @(
        "compose", "exec", "-T", "backend", "sh", "-c",
        'tar czf /tmp/diss_respaldo_docs.tar.gz -C /data documentos'
    ) | Out-Null
    Exec-Docker @("compose", "cp", "backend:/tmp/diss_respaldo_docs.tar.gz", $DocsDestino) | Out-Null
    Exec-Docker @("compose", "exec", "-T", "backend", "rm", "-f", "/tmp/diss_respaldo_docs.tar.gz") | Out-Null

    $hashBase = (Get-FileHash -Algorithm SHA256 -Path $BaseDestino).Hash
    $hashDocs = (Get-FileHash -Algorithm SHA256 -Path $DocsDestino).Hash

    @"
Respaldo del Sistema Municipal de Citas y Atenciones
Fecha: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
Base de datos: $BaseDestino
SHA256 base: $hashBase
Documentos: $DocsDestino
SHA256 documentos: $hashDocs
"@ | Set-Content -Path $Manifiesto -Encoding UTF8

    Write-Host "Respaldo creado:"
    Write-Host "  $BaseDestino"
    Write-Host "  $DocsDestino"
    Write-Host "  $Manifiesto"

    if (-not $Verificar) {
        return
    }

    Write-Host "Verificando restauracion en una base temporal..."
    try {
        Exec-Docker @("compose", "cp", $BaseDestino, "db:/tmp/diss_verificacion.dump") | Out-Null
        Exec-Docker @(
            "compose", "exec", "-T", "db", "sh", "-c",
            'createdb -U "$POSTGRES_USER" -T template0 "$1"', "sh", $BaseTemporal
        ) | Out-Null
        Exec-Docker @(
            "compose", "exec", "-T", "db", "sh", "-c",
            'pg_restore -U "$POSTGRES_USER" -d "$1" --no-owner /tmp/diss_verificacion.dump',
            "sh", $BaseTemporal
        ) | Out-Null

        $ConsultaConteos | Set-Content -Path $ArchivoSql -Encoding ASCII
        Exec-Docker @("compose", "cp", $ArchivoSql, "db:/tmp/diss_conteos.sql") | Out-Null

        $consultaVivos = 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -A -f /tmp/diss_conteos.sql'
        $consultaRestaurados = 'psql -U "$POSTGRES_USER" -d "' + $BaseTemporal + '" -t -A -f /tmp/diss_conteos.sql'

        $conteosVivos = Exec-Docker @(
            "compose", "exec", "-T", "db", "sh", "-c", $consultaVivos
        )
        $conteosRestaurados = Exec-Docker @(
            "compose", "exec", "-T", "db", "sh", "-c", $consultaRestaurados
        )

        if ([string]::IsNullOrWhiteSpace($conteosVivos) -or [string]::IsNullOrWhiteSpace($conteosRestaurados)) {
            throw "No se pudieron leer los conteos de las tablas."
        }

        if ($conteosVivos -ne $conteosRestaurados) {
            throw "Los conteos no coinciden. Origen: $conteosVivos. Restaurado: $conteosRestaurados."
        }

        Exec-Docker @("compose", "cp", $DocsDestino, "backend:/tmp/diss_verificacion_docs.tar.gz") | Out-Null
        Exec-Docker @(
            "compose", "exec", "-T", "backend", "sh", "-c",
            "rm -rf /tmp/diss_docs_verif && mkdir -p /tmp/diss_docs_verif && tar xzf /tmp/diss_verificacion_docs.tar.gz -C /tmp/diss_docs_verif"
        ) | Out-Null

        $documentosVivos = Contar-Documentos "/data/documentos"
        $documentosRestaurados = Contar-Documentos "/tmp/diss_docs_verif/documentos"

        if ($documentosVivos -ne $documentosRestaurados) {
            throw "Cantidad de documentos distinta. Origen: $documentosVivos. Restaurado: $documentosRestaurados."
        }

        $hashDocumentosVivos = Hash-Documentos "/data/documentos"
        $hashDocumentosRestaurados = Hash-Documentos "/tmp/diss_docs_verif/documentos"

        if ($hashDocumentosVivos -ne $hashDocumentosRestaurados) {
            throw "El contenido de los documentos no coincide."
        }

        Write-Host "Verificacion correcta:"
        Write-Host "  Conteos de tablas: $conteosRestaurados"
        Write-Host "  Documentos restaurados: $documentosRestaurados (contenido identico)"
    }
    finally {
        try {
            Exec-Docker @(
                "compose", "exec", "-T", "db", "sh", "-c",
                'dropdb -U "$POSTGRES_USER" --if-exists "$1"', "sh", $BaseTemporal
            ) | Out-Null
        }
        catch {
            Write-Warning "No se pudo eliminar la base temporal $BaseTemporal. $($_.Exception.Message)"
        }
        try {
            Exec-Docker @("compose", "exec", "-T", "db", "rm", "-f", "/tmp/diss_verificacion.dump", "/tmp/diss_conteos.sql") | Out-Null
            Exec-Docker @(
                "compose", "exec", "-T", "backend", "sh", "-c",
                "rm -rf /tmp/diss_docs_verif /tmp/diss_verificacion_docs.tar.gz"
            ) | Out-Null
            if (Test-Path $ArchivoSql) {
                Remove-Item -Force $ArchivoSql
            }
        }
        catch {
            Write-Warning "No se pudieron limpiar los archivos temporales de verificacion. $($_.Exception.Message)"
        }
    }
}
finally {
    Pop-Location
}
