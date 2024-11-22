<#
.Synopsis
Activate a Python virtual environment for the current PowerShell session.

.Description
Pushes the python executable for a virtual environment to the front of the
$Env:PATH environment variable and sets the prompt to signify that you are
in a Python virtual environment. Makes use of the command line switches as
well as the `pyvenv.cfg` file values present in the virtual environment.

.Parameter VenvDir
Path to the directory that contains the virtual environment to activate. The
default value for this is the parent of the directory that the Activate.ps1
script is located within.

.Parameter Prompt
The prompt prefix to display when this virtual environment is activated. By
default, this prompt is the name of the virtual environment folder (VenvDir)
surrounded by parentheses and followed by a single space (ie. '(.venv) ').

.Example
Activate.ps1
Activates the Python virtual environment that contains the Activate.ps1 script.

.Example
Activate.ps1 -Verbose
Activates the Python virtual environment that contains the Activate.ps1 script,
and shows extra information about the activation as it executes.

.Example
Activate.ps1 -VenvDir C:\Users\MyUser\Common\.venv
Activates the Python virtual environment located in the specified location.

.Example
Activate.ps1 -Prompt "MyPython"
Activates the Python virtual environment that contains the Activate.ps1 script,
and prefixes the current prompt with the specified string (surrounded in
parentheses) while the virtual environment is active.

.Notes
On Windows, it may be required to enable this Activate.ps1 script by setting the
execution policy for the user. You can do this by issuing the following PowerShell
command:

PS C:\> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

For more information on Execution Policies: 
https://go.microsoft.com/fwlink/?LinkID=135170

#>
Param(
    [Parameter(Mandatory = $false)]
    [String]
    $VenvDir,
    [Parameter(Mandatory = $false)]
    [String]
    $Prompt
)

<# Function declarations --------------------------------------------------- #>

<#
.Synopsis
Remove all shell session elements added by the Activate script, including the
addition of the virtual environment's Python executable from the beginning of
the PATH variable.

.Parameter NonDestructive
If present, do not remove this function from the global namespace for the
session.

#>
function global:deactivate ([switch]$NonDestructive) {
    # Revert to original values

    # The prior prompt:
    if (Test-Path -Path Function:_OLD_VIRTUAL_PROMPT) {
        Copy-Item -Path Function:_OLD_VIRTUAL_PROMPT -Destination Function:prompt
        Remove-Item -Path Function:_OLD_VIRTUAL_PROMPT
    }

    # The prior PYTHONHOME:
    if (Test-Path -Path Env:_OLD_VIRTUAL_PYTHONHOME) {
        Copy-Item -Path Env:_OLD_VIRTUAL_PYTHONHOME -Destination Env:PYTHONHOME
        Remove-Item -Path Env:_OLD_VIRTUAL_PYTHONHOME
    }

    # The prior PATH:
    if (Test-Path -Path Env:_OLD_VIRTUAL_PATH) {
        Copy-Item -Path Env:_OLD_VIRTUAL_PATH -Destination Env:PATH
        Remove-Item -Path Env:_OLD_VIRTUAL_PATH
    }

    # Just remove the VIRTUAL_ENV altogether:
    if (Test-Path -Path Env:VIRTUAL_ENV) {
        Remove-Item -Path env:VIRTUAL_ENV
    }

    # Just remove the _PYTHON_VENV_PROMPT_PREFIX altogether:
    if (Get-Variable -Name "_PYTHON_VENV_PROMPT_PREFIX" -ErrorAction SilentlyContinue) {
        Remove-Variable -Name _PYTHON_VENV_PROMPT_PREFIX -Scope Global -Force
    }

    # Leave deactivate function in the global namespace if requested:
    if (-not $NonDestructive) {
        Remove-Item -Path function:deactivate
    }
}

<#
.Description
Get-PyVenvConfig parses the values from the pyvenv.cfg file located in the
given folder, and returns them in a map.

For each line in the pyvenv.cfg file, if that line can be parsed into exactly
two strings separated by `=` (with any amount of whitespace surrounding the =)
then it is considered a `key = value` line. The left hand string is the key,
the right hand is the value.

If the value starts with a `'` or a `"` then the first and last character is
stripped from the value before being captured.

.Parameter ConfigDir
Path to the directory that contains the `pyvenv.cfg` file.
#>
function Get-PyVenvConfig(
    [String]
    $ConfigDir
) {
    Write-Verbose "Given ConfigDir=$ConfigDir, obtain values in pyvenv.cfg"

    # Ensure the file exists, and issue a warning if it doesn't (but still allow the function to continue).
    $pyvenvConfigPath = Join-Path -Resolve -Path $ConfigDir -ChildPath 'pyvenv.cfg' -ErrorAction Continue

    # An empty map will be returned if no config file is found.
    $pyvenvConfig = @{ }

    if ($pyvenvConfigPath) {

        Write-Verbose "File exists, parse `key = value` lines"
        $pyvenvConfigContent = Get-Content -Path $pyvenvConfigPath

        $pyvenvConfigContent | ForEach-Object {
            $keyval = $PSItem -split "\s*=\s*", 2
            if ($keyval[0] -and $keyval[1]) {
                $val = $keyval[1]

                # Remove extraneous quotations around a string value.
                if ("'""".Contains($val.Substring(0, 1))) {
                    $val = $val.Substring(1, $val.Length - 2)
                }

                $pyvenvConfig[$keyval[0]] = $val
                Write-Verbose "Adding Key: '$($keyval[0])'='$val'"
            }
        }
    }
    return $pyvenvConfig
}


<# Begin Activate script --------------------------------------------------- #>

# Determine the containing directory of this script
$VenvExecPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
$VenvExecDir = Get-Item -Path $VenvExecPath

Write-Verbose "Activation script is located in path: '$VenvExecPath'"
Write-Verbose "VenvExecDir Fullname: '$($VenvExecDir.FullName)"
Write-Verbose "VenvExecDir Name: '$($VenvExecDir.Name)"

# Set values required in priority: CmdLine, ConfigFile, Default
# First, get the location of the virtual environment, it might not be
# VenvExecDir if specified on the command line.
if ($VenvDir) {
    Write-Verbose "VenvDir given as parameter, using '$VenvDir' to determine values"
}
else {
    Write-Verbose "VenvDir not given as a parameter, using parent directory name as VenvDir."
    $VenvDir = $VenvExecDir.Parent.FullName.TrimEnd("\\/")
    Write-Verbose "VenvDir=$VenvDir"
}

# Next, read the `pyvenv.cfg` file to determine any required value such
# as `prompt`.
$pyvenvCfg = Get-PyVenvConfig -ConfigDir $VenvDir

# Next, set the prompt from the command line, or the config file, or
# just use the name of the virtual environment folder.
if ($Prompt) {
    Write-Verbose "Prompt specified as argument, using '$Prompt'"
}
else {
    Write-Verbose "Prompt not specified as argument to script, checking pyvenv.cfg value"
    if ($pyvenvCfg -and $pyvenvCfg['prompt']) {
        Write-Verbose "  Setting based on value in pyvenv.cfg='$($pyvenvCfg['prompt'])'"
        $Prompt = $pyvenvCfg['prompt'];
    }
    else {
        Write-Verbose "  Setting prompt based on parent's directory's name. (Is the directory name passed to venv module when creating the virutal environment)"
        Write-Verbose "  Got leaf-name of $VenvDir='$(Split-Path -Path $venvDir -Leaf)'"
        $Prompt = Split-Path -Path $venvDir -Leaf
    }
}

Write-Verbose "Prompt = '$Prompt'"
Write-Verbose "VenvDir='$VenvDir'"

# Deactivate any currently active virtual environment, but leave the
# deactivate function in place.
deactivate -nondestructive

# Now set the environment variable VIRTUAL_ENV, used by many tools to determine
# that there is an activated venv.
$env:VIRTUAL_ENV = $VenvDir

if (-not $Env:VIRTUAL_ENV_DISABLE_PROMPT) {

    Write-Verbose "Setting prompt to '$Prompt'"

    # Set the prompt to include the env name
    # Make sure _OLD_VIRTUAL_PROMPT is global
    function global:_OLD_VIRTUAL_PROMPT { "" }
    Copy-Item -Path function:prompt -Destination function:_OLD_VIRTUAL_PROMPT
    New-Variable -Name _PYTHON_VENV_PROMPT_PREFIX -Description "Python virtual environment prompt prefix" -Scope Global -Option ReadOnly -Visibility Public -Value $Prompt

    function global:prompt {
        Write-Host -NoNewline -ForegroundColor Green "($_PYTHON_VENV_PROMPT_PREFIX) "
        _OLD_VIRTUAL_PROMPT
    }
}

# Clear PYTHONHOME
if (Test-Path -Path Env:PYTHONHOME) {
    Copy-Item -Path Env:PYTHONHOME -Destination Env:_OLD_VIRTUAL_PYTHONHOME
    Remove-Item -Path Env:PYTHONHOME
}

# Add the venv to the PATH
Copy-Item -Path Env:PATH -Destination Env:_OLD_VIRTUAL_PATH
$Env:PATH = "$VenvExecDir$([System.IO.Path]::PathSeparator)$Env:PATH"

# SIG # Begin signature block
# MIIeSQYJKoZIhvcNAQcCoIIeOjCCHjYCAQExDzANBglghkgBZQMEAgEFADB5Bgor
# BgEEAYI3AgEEoGswaTA0BgorBgEEAYI3AgEeMCYCAwEAAAQQH8w7YFlLCE63JNLG
# KX7zUQIBAAIBAAIBAAIBAAIBADAxMA0GCWCGSAFlAwQCAQUABCAwnDYwEHaCQq0n
# 8NAvsN7H7BO7/48rXCNwrg891FS5vaCCC38wggUwMIIEGKADAgECAhAECRgbX9W7
# ZnVTQ7VvlVAIMA0GCSqGSIb3DQEBCwUAMGUxCzAJBgNVBAYTAlVTMRUwEwYDVQQK
# EwxEaWdpQ2VydCBJbmMxGTAXBgNVBAsTEHd3dy5kaWdpY2VydC5jb20xJDAiBgNV
# BAMTG0RpZ2lDZXJ0IEFzc3VyZWQgSUQgUm9vdCBDQTAeFw0xMzEwMjIxMjAwMDBa
# Fw0yODEwMjIxMjAwMDBaMHIxCzAJBgNVBAYTAlVTMRUwEwYDVQQKEwxEaWdpQ2Vy
# dCBJbmMxGTAXBgNVBAsTEHd3dy5kaWdpY2VydC5jb20xMTAvBgNVBAMTKERpZ2lD
# ZXJ0IFNIQTIgQXNzdXJlZCBJRCBDb2RlIFNpZ25pbmcgQ0EwggEiMA0GCSqGSIb3
# DQEBAQUAA4IBDwAwggEKAoIBAQD407Mcfw4Rr2d3B9MLMUkZz9D7RZmxOttE9X/l
# qJ3bMtdx6nadBS63j/qSQ8Cl+YnUNxnXtqrwnIal2CWsDnkoOn7p0WfTxvspJ8fT
# eyOU5JEjlpB3gvmhhCNmElQzUHSxKCa7JGnCwlLyFGeKiUXULaGj6YgsIJWuHEqH
# CN8M9eJNYBi+qsSyrnAxZjNxPqxwoqvOf+l8y5Kh5TsxHM/q8grkV7tKtel05iv+
# bMt+dDk2DZDv5LVOpKnqagqrhPOsZ061xPeM0SAlI+sIZD5SlsHyDxL0xY4PwaLo
# LFH3c7y9hbFig3NBggfkOItqcyDQD2RzPJ6fpjOp/RnfJZPRAgMBAAGjggHNMIIB
# yTASBgNVHRMBAf8ECDAGAQH/AgEAMA4GA1UdDwEB/wQEAwIBhjATBgNVHSUEDDAK
# BggrBgEFBQcDAzB5BggrBgEFBQcBAQRtMGswJAYIKwYBBQUHMAGGGGh0dHA6Ly9v
# Y3NwLmRpZ2ljZXJ0LmNvbTBDBggrBgEFBQcwAoY3aHR0cDovL2NhY2VydHMuZGln
# aWNlcnQuY29tL0RpZ2lDZXJ0QXNzdXJlZElEUm9vdENBLmNydDCBgQYDVR0fBHow
# eDA6oDigNoY0aHR0cDovL2NybDQuZGlnaWNlcnQuY29tL0RpZ2lDZXJ0QXNzdXJl
# ZElEUm9vdENBLmNybDA6oDigNoY0aHR0cDovL2NybDMuZGlnaWNlcnQuY29tL0Rp
# Z2lDZXJ0QXNzdXJlZElEUm9vdENBLmNybDBPBgNVHSAESDBGMDgGCmCGSAGG/WwA
# AgQwKjAoBggrBgEFBQcCARYcaHR0cHM6Ly93d3cuZGlnaWNlcnQuY29tL0NQUzAK
# BghghkgBhv1sAzAdBgNVHQ4EFgQUWsS5eyoKo6XqcQPAYPkt9mV1DlgwHwYDVR0j
# BBgwFoAUReuir/SSy4IxLVGLp6chnfNtyA8wDQYJKoZIhvcNAQELBQADggEBAD7s
# DVoks/Mi0RXILHwlKXaoHV0cLToaxO8wYdd+C2D9wz0PxK+L/e8q3yBVN7Dh9tGS
# dQ9RtG6ljlriXiSBThCk7j9xjmMOE0ut119EefM2FAaK95xGTlz/kLEbBw6RFfu6
# r7VRwo0kriTGxycqoSkoGjpxKAI8LpGjwCUR4pwUR6F6aGivm6dcIFzZcbEMj7uo
# +MUSaJ/PQMtARKUT8OZkDCUIQjKyNookAv4vcn4c10lFluhZHen6dGRrsutmQ9qz
# sIzV6Q3d9gEgzpkxYz0IGhizgZtPxpMQBvwHgfqL2vmCSfdibqFT+hKUGIUukpHq
# aGxEMrJmoecYpJpkUe8wggZHMIIFL6ADAgECAhADPtXtoGXRuMkd/PkqbJvYMA0G
# CSqGSIb3DQEBCwUAMHIxCzAJBgNVBAYTAlVTMRUwEwYDVQQKEwxEaWdpQ2VydCBJ
# bmMxGTAXBgNVBAsTEHd3dy5kaWdpY2VydC5jb20xMTAvBgNVBAMTKERpZ2lDZXJ0
# IFNIQTIgQXNzdXJlZCBJRCBDb2RlIFNpZ25pbmcgQ0EwHhcNMTgxMjE4MDAwMDAw
# WhcNMjExMjIyMTIwMDAwWjCBgzELMAkGA1UEBhMCVVMxFjAUBgNVBAgTDU5ldyBI
# YW1wc2hpcmUxEjAQBgNVBAcTCVdvbGZlYm9ybzEjMCEGA1UEChMaUHl0aG9uIFNv
# ZnR3YXJlIEZvdW5kYXRpb24xIzAhBgNVBAMTGlB5dGhvbiBTb2Z0d2FyZSBGb3Vu
# ZGF0aW9uMIICIjANBgkqhkiG9w0BAQEFAAOCAg8AMIICCgKCAgEAqr2kS7J1uW7o
# JRxlsdrETAjKarfoH5TI8PWST6Yb2xPooP7vHT4iaVXyL5Lze1f53Jw67Sp+u524
# fJXf30qHViEWxumy2RWG0nciU2d+mMqzjlaAWSZNF0u4RcvyDJokEV0RUOqI5CG5
# zPI3W9uQ6LiUk3HCYW6kpH177A5T3pw/Po8O8KErJGn1anaqtIICq99ySxrMad/2
# hPMBRf6Ndah7f7HPn1gkSSTAoejyuqF5h+B0qI4+JK5+VLvz659VTbAWJsYakkxZ
# xVWYpFv4KeQSSwoo0DzMvmERsTzNvVBMWhu9OriJNg+QfFmf96zVTu93cZ+r7xMp
# bXyfIOGKhHMaRuZ8ihuWIx3gI9WHDFX6fBKR8+HlhdkaiBEWIsXRoy+EQUyK7zUs
# +FqOo2sRYttbs8MTF9YDKFZwyPjn9Wn+gLGd5NUEVyNvD9QVGBEtN7vx87bduJUB
# 8F4DylEsMtZTfjw/au6AmOnmneK5UcqSJuwRyZaGNk7y3qj06utx+HTTqHgi975U
# pxfyrwAqkovoZEWBVSpvku8PVhkBXcLmNe6MEHlFiaMoiADAeKmX5RFRkN+VrmYG
# Tg4zajxfdHeIY8TvLf48tTfmnQJd98geJQv/01NUy/FxuwqAuTkaez5Nl1LxP0Cp
# THhghzO4FRD4itT2wqTh4jpojw9QZnsCAwEAAaOCAcUwggHBMB8GA1UdIwQYMBaA
# FFrEuXsqCqOl6nEDwGD5LfZldQ5YMB0GA1UdDgQWBBT8Kr9+1L6s84KcpM97IgE7
# uI8H8jAOBgNVHQ8BAf8EBAMCB4AwEwYDVR0lBAwwCgYIKwYBBQUHAwMwdwYDVR0f
# BHAwbjA1oDOgMYYvaHR0cDovL2NybDMuZGlnaWNlcnQuY29tL3NoYTItYXNzdXJl
# ZC1jcy1nMS5jcmwwNaAzoDGGL2h0dHA6Ly9jcmw0LmRpZ2ljZXJ0LmNvbS9zaGEy
# LWFzc3VyZWQtY3MtZzEuY3JsMEwGA1UdIARFMEMwNwYJYIZIAYb9bAMBMCowKAYI
# KwYBBQUHAgEWHGh0dHBzOi8vd3d3LmRpZ2ljZXJ0LmNvbS9DUFMwCAYGZ4EMAQQB
# MIGEBggrBgEFBQcBAQR4MHYwJAYIKwYBBQUHMAGGGGh0dHA6Ly9vY3NwLmRpZ2lj
# ZXJ0LmNvbTBOBggrBgEFBQcwAoZCaHR0cDovL2NhY2VydHMuZGlnaWNlcnQuY29t
# L0RpZ2lDZXJ0U0hBMkFzc3VyZWRJRENvZGVTaWduaW5nQ0EuY3J0MAwGA1UdEwEB
# /wQCMAAwDQYJKoZIhvcNAQELBQADggEBAEt1oS21X0axiafPjyY+vlYqjWKuUu/Y
# FuYWIEq6iRRaFabNDhj9RBFQF/aJiE5msrQEOfAD6/6gVSH91lZWBqg6NEeG9T9S
# XbiAPvJ9CEWFsdkXUrjbWhvCnuZ7kqUuU5BAumI1QRbpYgZL3UA+iZXkmjbGh1ln
# 8rUhWIxbBYL4Sg2nqpB44p7CUFYkPj/MbwU2gvBV2pXjj5WaskoZtsACMv5g42BN
# oVLoRAi+ev6s07POt+JtHRIm87lTyuc8wh0swTPUwksKbLU1Zdj9CpqtzXnuVE0w
# 50exJvRSK3Vt4g+0vigpI3qPmDdpkf9+4Mvy0XMNcqrthw20R+PkIlMxghIgMIIS
# HAIBATCBhjByMQswCQYDVQQGEwJVUzEVMBMGA1UEChMMRGlnaUNlcnQgSW5jMRkw
# FwYDVQQLExB3d3cuZGlnaWNlcnQuY29tMTEwLwYDVQQDEyhEaWdpQ2VydCBTSEEy
# IEFzc3VyZWQgSUQgQ29kZSBTaWduaW5nIENBAhADPtXtoGXRuMkd/PkqbJvYMA0G
# CWCGSAFlAwQCAQUAoIGeMBkGCSqGSIb3DQEJAzEMBgorBgEEAYI3AgEEMBwGCisG
# AQQBgjcCAQsxDjAMBgorBgEEAYI3AgEVMC8GCSqGSIb3DQEJBDEiBCAGueLiZxG/
# uwwkezGlE6NGik7PbC5BWsmef6UPtfvL6DAyBgorBgEEAYI3AgEMMSQwIqAggB4A
# UAB5AHQAaABvAG4AIAAzAC4AOQAuADEAcgBjADEwDQYJKoZIhvcNAQEBBQAEggIA
# IhtjiHQL/XmW5zgzcpm/Yd36JAaPEkZYrWyeOAMlA7A3ufNXa9VhrgbEsqYn7Uoa
# 7siKSDbryYickMn1muQ+W8OLhv6vHnQEsRdbEtdIoOcTFhd7aZKoWdz4uUBieix1
# 2xuZAP+HcBawb+hX9sSfFcFQ8IslAzKXd7gt1pFsvyXJSp9mm2z0Qqg5oBv2oaUe
# Drpn1GPgmEmBHkNL7mmPtuAlu/vfVHl5VjOvsX5SynUEOBH+w8ZI63itwF4a39/z
# MFAsjsV30lILVv5OJeI66UrwnsOtgluRts5OhB+6hD1In+wJBPRLC80RspmdQibr
# Uapj9mM3tAsFqI2tR1LQe3oRkgEJHR10vzxknEAItz5n2v4hMvxh5qe/L9LeOUVy
# 85lYXrjseLWEkm/dfwbyY6n2EtExW9b0PYh0uS7SshME+p3cj6XL3APUZ4N/USL9
# zPUDJs+LMupGxmyx+IxdPBki3xBov1yTG/XHhUqYx62c3rF22Hoe5JG3ojuE/yXb
# yAIRAgdFAoNSQon3yPJybQ0wa3B2LLPzsYqbLUuJL4KEvAKj7qcJxCEU3t6KgzJd
# ocycS03rBmQoCNEt/lxUykGj846o617p3crpkmrYbSzjoF2THrMkQpaICzcaLq6b
# DHED6BEy+TeJ6szZCml+zzpobcpBROC4bJjg82U7SEChgg7JMIIOxQYKKwYBBAGC
# NwMDATGCDrUwgg6xBgkqhkiG9w0BBwKggg6iMIIOngIBAzEPMA0GCWCGSAFlAwQC
# AQUAMHgGCyqGSIb3DQEJEAEEoGkEZzBlAgEBBglghkgBhv1sBwEwMTANBglghkgB
# ZQMEAgEFAAQgq8/fuFqlNsI+krjAb0CtDieNKpjCPANpYlE2xGCZfnYCEQCH/v1I
# EzB+xn4bOA2QtfMhGA8yMDIwMTEyNDE5NTE0OFqgggu7MIIGgjCCBWqgAwIBAgIQ
# BM0/hWiudsYbsP5xYMynbTANBgkqhkiG9w0BAQsFADByMQswCQYDVQQGEwJVUzEV
# MBMGA1UEChMMRGlnaUNlcnQgSW5jMRkwFwYDVQQLExB3d3cuZGlnaWNlcnQuY29t
# MTEwLwYDVQQDEyhEaWdpQ2VydCBTSEEyIEFzc3VyZWQgSUQgVGltZXN0YW1waW5n
# IENBMB4XDTE5MTAwMTAwMDAwMFoXDTMwMTAxNzAwMDAwMFowTDELMAkGA1UEBhMC
# VVMxFzAVBgNVBAoTDkRpZ2lDZXJ0LCBJbmMuMSQwIgYDVQQDExtUSU1FU1RBTVAt
# U0hBMjU2LTIwMTktMTAtMTUwggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAwggEKAoIB
# AQDpZDWc+qmYZWQb5BfcuCk2zGcJWIVNMODJ/+U7PBEoUK8HMeJdCRjC9omMaQgE
# I+B3LZ0V5bjooWqO/9Su0noW7/hBtR05dcHPL6esRX6UbawDAZk8Yj5+ev1FlzG0
# +rfZQj6nVZvfWk9YAqgyaSITvouCLcaYq2ubtMnyZREMdA2y8AiWdMToskiioRSl
# +PrhiXBEO43v+6T0w7m9FCzrDCgnJYCrEEsWEmALaSKMTs3G1bJlWSHgfCwSjXAO
# j4rK4NPXszl3UNBCLC56zpxnejh3VED/T5UEINTryM6HFAj+HYDd0OcreOq/H3DG
# 7kIWUzZFm1MZSWKdegKblRSjAgMBAAGjggM4MIIDNDAOBgNVHQ8BAf8EBAMCB4Aw
# DAYDVR0TAQH/BAIwADAWBgNVHSUBAf8EDDAKBggrBgEFBQcDCDCCAb8GA1UdIASC
# AbYwggGyMIIBoQYJYIZIAYb9bAcBMIIBkjAoBggrBgEFBQcCARYcaHR0cHM6Ly93
# d3cuZGlnaWNlcnQuY29tL0NQUzCCAWQGCCsGAQUFBwICMIIBVh6CAVIAQQBuAHkA
# IAB1AHMAZQAgAG8AZgAgAHQAaABpAHMAIABDAGUAcgB0AGkAZgBpAGMAYQB0AGUA
# IABjAG8AbgBzAHQAaQB0AHUAdABlAHMAIABhAGMAYwBlAHAAdABhAG4AYwBlACAA
# bwBmACAAdABoAGUAIABEAGkAZwBpAEMAZQByAHQAIABDAFAALwBDAFAAUwAgAGEA
# bgBkACAAdABoAGUAIABSAGUAbAB5AGkAbgBnACAAUABhAHIAdAB5ACAAQQBnAHIA
# ZQBlAG0AZQBuAHQAIAB3AGgAaQBjAGgAIABsAGkAbQBpAHQAIABsAGkAYQBiAGkA
# bABpAHQAeQAgAGEAbgBkACAAYQByAGUAIABpAG4AYwBvAHIAcABvAHIAYQB0AGUA
# ZAAgAGgAZQByAGUAaQBuACAAYgB5ACAAcgBlAGYAZQByAGUAbgBjAGUALjALBglg
# hkgBhv1sAxUwHwYDVR0jBBgwFoAU9LbhIB3+Ka7S5GGlsqIlssgXNW4wHQYDVR0O
# BBYEFFZTD8HGB6dN19huV3KAUEzk7J7BMHEGA1UdHwRqMGgwMqAwoC6GLGh0dHA6
# Ly9jcmwzLmRpZ2ljZXJ0LmNvbS9zaGEyLWFzc3VyZWQtdHMuY3JsMDKgMKAuhixo
# dHRwOi8vY3JsNC5kaWdpY2VydC5jb20vc2hhMi1hc3N1cmVkLXRzLmNybDCBhQYI
# KwYBBQUHAQEEeTB3MCQGCCsGAQUFBzABhhhodHRwOi8vb2NzcC5kaWdpY2VydC5j
# b20wTwYIKwYBBQUHMAKGQ2h0dHA6Ly9jYWNlcnRzLmRpZ2ljZXJ0LmNvbS9EaWdp
# Q2VydFNIQTJBc3N1cmVkSURUaW1lc3RhbXBpbmdDQS5jcnQwDQYJKoZIhvcNAQEL
# BQADggEBAC6DoUQFSgTjuTJS+tmB8Bq7+AmNI7k92JKh5kYcSi9uejxjbjcXoxq/
# WCOyQ5yUg045CbAs6Mfh4szty3lrzt4jAUftlVSB4IB7ErGvAoapOnNq/vifwY3R
# IYzkKYLDigtgAAKdH0fEn7QKaFN/WhCm+CLm+FOSMV/YgoMtbRNCroPBEE6kJPRH
# nN4PInJ3XH9P6TmYK1eSRNfvbpPZQ8cEM2NRN1aeRwQRw6NYVCHY4o5W10k/V/wK
# nyNee/SUjd2dGrvfeiqm0kWmVQyP9kyK8pbPiUbcMbKRkKNfMzBgVfX8azCsoe3k
# R04znmdqKLVNwu1bl4L4y6kIbFMJtPcwggUxMIIEGaADAgECAhAKoSXW1jIbfkHk
# Bdo2l8IVMA0GCSqGSIb3DQEBCwUAMGUxCzAJBgNVBAYTAlVTMRUwEwYDVQQKEwxE
# aWdpQ2VydCBJbmMxGTAXBgNVBAsTEHd3dy5kaWdpY2VydC5jb20xJDAiBgNVBAMT
# G0RpZ2lDZXJ0IEFzc3VyZWQgSUQgUm9vdCBDQTAeFw0xNjAxMDcxMjAwMDBaFw0z
# MTAxMDcxMjAwMDBaMHIxCzAJBgNVBAYTAlVTMRUwEwYDVQQKEwxEaWdpQ2VydCBJ
# bmMxGTAXBgNVBAsTEHd3dy5kaWdpY2VydC5jb20xMTAvBgNVBAMTKERpZ2lDZXJ0
# IFNIQTIgQXNzdXJlZCBJRCBUaW1lc3RhbXBpbmcgQ0EwggEiMA0GCSqGSIb3DQEB
# AQUAA4IBDwAwggEKAoIBAQC90DLuS82Pf92puoKZxTlUKFe2I0rEDgdFM1EQfdD5
# fU1ofue2oPSNs4jkl79jIZCYvxO8V9PD4X4I1moUADj3Lh477sym9jJZ/l9lP+Cb
# 6+NGRwYaVX4LJ37AovWg4N4iPw7/fpX786O6Ij4YrBHk8JkDbTuFfAnT7l3ImgtU
# 46gJcWvgzyIQD3XPcXJOCq3fQDpct1HhoXkUxk0kIzBdvOw8YGqsLwfM/fDqR9mI
# UF79Zm5WYScpiYRR5oLnRlD9lCosp+R1PrqYD4R/nzEU1q3V8mTLex4F0IQZchfx
# FwbvPc3WTe8GQv2iUypPhR3EHTyvz9qsEPXdrKzpVv+TAgMBAAGjggHOMIIByjAd
# BgNVHQ4EFgQU9LbhIB3+Ka7S5GGlsqIlssgXNW4wHwYDVR0jBBgwFoAUReuir/SS
# y4IxLVGLp6chnfNtyA8wEgYDVR0TAQH/BAgwBgEB/wIBADAOBgNVHQ8BAf8EBAMC
# AYYwEwYDVR0lBAwwCgYIKwYBBQUHAwgweQYIKwYBBQUHAQEEbTBrMCQGCCsGAQUF
# BzABhhhodHRwOi8vb2NzcC5kaWdpY2VydC5jb20wQwYIKwYBBQUHMAKGN2h0dHA6
# Ly9jYWNlcnRzLmRpZ2ljZXJ0LmNvbS9EaWdpQ2VydEFzc3VyZWRJRFJvb3RDQS5j
# cnQwgYEGA1UdHwR6MHgwOqA4oDaGNGh0dHA6Ly9jcmw0LmRpZ2ljZXJ0LmNvbS9E
# aWdpQ2VydEFzc3VyZWRJRFJvb3RDQS5jcmwwOqA4oDaGNGh0dHA6Ly9jcmwzLmRp
# Z2ljZXJ0LmNvbS9EaWdpQ2VydEFzc3VyZWRJRFJvb3RDQS5jcmwwUAYDVR0gBEkw
# RzA4BgpghkgBhv1sAAIEMCowKAYIKwYBBQUHAgEWHGh0dHBzOi8vd3d3LmRpZ2lj
# ZXJ0LmNvbS9DUFMwCwYJYIZIAYb9bAcBMA0GCSqGSIb3DQEBCwUAA4IBAQBxlRLp
# UYdWac3v3dp8qmN6s3jPBjdAhO9LhL/KzwMC/cWnww4gQiyvd/MrHwwhWiq3BTQd
# aq6Z+CeiZr8JqmDfdqQ6kw/4stHYfBli6F6CJR7Euhx7LCHi1lssFDVDBGiy23UC
# 4HLHmNY8ZOUfSBAYX4k4YU1iRiSHY4yRUiyvKYnleB/WCxSlgNcSR3CzddWThZN+
# tpJn+1Nhiaj1a5bA9FhpDXzIAbG5KHW3mWOFIoxhynmUfln8jA/jb7UBJrZspe6H
# USHkWGCbugwtK22ixH67xCUrRwIIfEmuE7bhfEJCKMYYVs9BNLZmXbZ0e/VWMyIv
# IjayS6JKldj1po5SMYICTTCCAkkCAQEwgYYwcjELMAkGA1UEBhMCVVMxFTATBgNV
# BAoTDERpZ2lDZXJ0IEluYzEZMBcGA1UECxMQd3d3LmRpZ2ljZXJ0LmNvbTExMC8G
# A1UEAxMoRGlnaUNlcnQgU0hBMiBBc3N1cmVkIElEIFRpbWVzdGFtcGluZyBDQQIQ
# BM0/hWiudsYbsP5xYMynbTANBglghkgBZQMEAgEFAKCBmDAaBgkqhkiG9w0BCQMx
# DQYLKoZIhvcNAQkQAQQwHAYJKoZIhvcNAQkFMQ8XDTIwMTEyNDE5NTE0OFowKwYL
# KoZIhvcNAQkQAgwxHDAaMBgwFgQUAyW9UF7aljAtwi9PoB5MKL4oNMUwLwYJKoZI
# hvcNAQkEMSIEIDn6i0vu2C7fmj4cAD/fDlc1VopzVkrtA5XUlxiGIqA6MA0GCSqG
# SIb3DQEBAQUABIIBADnNeFkaLUliZCvLQp4ck6xDwTyio9Mxh7F/TBMXtMXDAkyg
# r082ctQBM9STfNUtqAF9CVceKNZEw1TGB64iTQpZdYZFHhHq771tailh6Wh2YA6E
# 3n7nolI4hWj86fRRZlGvnzxUcHPC5adD8XAGvjpDJK16EsHxvWHks+0aMIJeAeOb
# ja5WpHWZO1Xp9CQvmvINYueF6tTPyfMW6v9TfLNwDExbPg51n4XTT3kDZLKnUvz5
# SKnSz/TsJFZOEHE1FOWZTtbIHaoLbR2lmGwViFrsk2w7Fm3q47ENdzwa4PrwvamS
# jg8vIikeVLjnqajTe+enJOdvnWIZqeKPz2JiCFk=
# SIG # End signature block
