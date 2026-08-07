/*
    MEMFORENSIX - Suspicious Indicator Rules
    Generic heuristic rules for demo/educational use. Not a substitute
    for a maintained threat-intel feed in production.
*/

rule Possible_C2_Beacon_String : c2 network
{
    meta:
        description = "Strings commonly seen in C2 beacon configs"
        severity = "high"
        author = "memforensix"
    strings:
        $s1 = "User-Agent: Mozilla/4.0 (compatible; MSIE" nocase
        $s2 = "beacon" nocase
        $s3 = "/gate.php"
        $s4 = "cmd.exe /c" nocase
    condition:
        2 of them
}

rule Possible_Process_Hollowing_API_Cluster : process_injection
{
    meta:
        description = "API name cluster frequently used together for process hollowing"
        severity = "high"
        author = "memforensix"
    strings:
        $a1 = "NtUnmapViewOfSection"
        $a2 = "WriteProcessMemory"
        $a3 = "SetThreadContext"
        $a4 = "ResumeThread"
        $a5 = "CreateProcessA"
    condition:
        4 of them
}

rule Suspicious_PowerShell_Encoded_Command : powershell fileless
{
    meta:
        description = "Base64-encoded PowerShell execution flags, common in fileless malware"
        severity = "medium"
        author = "memforensix"
    strings:
        $p1 = "-enc " nocase
        $p2 = "-EncodedCommand" nocase
        $p3 = "-nop -w hidden" nocase
        $p4 = "IEX(New-Object" nocase
    condition:
        any of them
}

rule Packer_UPX_Signature : packer
{
    meta:
        description = "UPX packer section markers"
        severity = "low"
        author = "memforensix"
    strings:
        $upx1 = "UPX0"
        $upx2 = "UPX1"
        $upx3 = "UPX!"
    condition:
        2 of them
}

rule Mimikatz_Artifacts : credential_theft
{
    meta:
        description = "Strings associated with the Mimikatz credential-dumping tool"
        severity = "critical"
        author = "memforensix"
    strings:
        $m1 = "sekurlsa::logonpasswords" nocase
        $m2 = "mimikatz" nocase
        $m3 = "gentilkiwi" nocase
    condition:
        any of them
}

rule Suspicious_Outbound_Tor_Indicator : anonymization network
{
    meta:
        description = "Strings indicating Tor / anonymization network usage"
        severity = "medium"
        author = "memforensix"
    strings:
        $t1 = ".onion" nocase
        $t2 = "tor-resolve" nocase
    condition:
        any of them
}
