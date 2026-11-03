# Restauracion de la base de datos y del volumen de documentos.
#
# ADVERTENCIA: reemplaza la base de desarrollo y los documentos actuales.
# Requiere el modificador -Confirmar para ejecutarse.
#
# Uso:
#   .\scripts\restauracion.ps1 -Base .\respaldos\base_20261102_120000.dump `
#       -Documentos .\respaldos\documentos_20261102_120000.tar.gz -Confirmar
#
# El respaldo puede haberse creado con scripts\respaldo.ps1.
# Para probar la restauracion sin tocar los datos reales use:
#   .\scripts\respaldo.ps1 -Verificar

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$Base,
    [string]$Documentos,
    [switch]$Confirmar
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not $Confirmar) {
    Write-Host "Restauracion cancelada."
    Write-Host "Esta operacion reemplaza la base de datos y los documentos actuales."
    Write-Host "Vuelva a ejecutar con -Confirmar si realmente desea continuar."
    exit 1
}

$Raiz = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Base = (Resolve-Path $Base).Path
if ($Documentos) {
    $Documentos = (Resolve-Path $Documentos).Path
}

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

Push-Location $Raiz
try {
    Write-Host "Deteniendo el backend para restaurar sin conexiones activas..."
    Exec-Docker @("compose", "stop", "backend") | Out-Null

    try {
        Write-Host "Restaurando la base de datos..."
        Exec-Docker @("compose", "cp", $Base, "db:/tmp/diss_restauracion.dump") | Out-Null
        Exec-Docker @(
            "compose", "exec", "-T", "db", "sh", "-c",
            'pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists --no-owner /tmp/diss_restauracion.dump'
        ) | Out-Null

        if ($Documentos) {
            Write-Host "Restaurando los documentos..."
            Exec-Docker @("compose", "cp", $Documentos, "backend:/tmp/diss_restauracion_docs.tar.gz") | Out-Null
            # /data/documentos es el punto de montaje del volumen: no se puede
            # eliminar. Se extrae primero a un directorio temporal y solo si la
            # extraccion funciona se reemplaza el contenido del volumen.
            Exec-Docker @(
                "compose", "exec", "-T", "backend", "sh", "-c",
                "rm -rf /data/documentos_nuevo && mkdir -p /data/documentos_nuevo && tar xzf /tmp/diss_restauracion_docs.tar.gz -C /data/documentos_nuevo --strip-components=1 && find /data/documentos -mindepth 1 -delete && cp -a /data/documentos_nuevo/. /data/documentos/ && rm -rf /data/documentos_nuevo"
            ) | Out-Null
            Exec-Docker @("compose", "exec", "-T", "backend", "rm", "-f", "/tmp/diss_restauracion_docs.tar.gz") | Out-Null
        }
        else {
            Write-Warning "No se indico -Documentos: solo se restauro la base de datos."
        }
    }
    finally {
        Exec-Docker @("compose", "exec", "-T", "db", "rm", "-f", "/tmp/diss_restauracion.dump") | Out-Null
        Write-Host "Iniciando el backend..."
        Exec-Docker @("compose", "start", "backend") | Out-Null
    }

    Write-Host "Esperando a que la API responda..."
    $listo = $false
    for ($intento = 1; $intento -le 20; $intento++) {
        try {
            $respuesta = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/health" -TimeoutSec 3
            if ($respuesta.estado -eq "ok") {
                $listo = $true
                break
            }
        }
        catch {
            Start-Sleep -Seconds 2
        }
    }

    if (-not $listo) {
        throw "La API no respondio despues de la restauracion. Revise 'docker compose logs backend'."
    }

    Write-Host "Restauracion completada. La API responde correctamente."
}
finally {
    Pop-Location
}
