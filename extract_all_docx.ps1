param(
    [string]$InputDir = ".",
    [string]$OutputDir = "extracted_text"
)

# Create output directory
if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir | Out-Null
}

# Get all CCNA docx files
$docxFiles = Get-ChildItem -Path $InputDir -Filter "CCNA_*.docx"
Write-Host "Found $($docxFiles.Count) CCNA docx files"

foreach ($file in $docxFiles) {
    $baseName = $file.BaseName
    $outputFile = Join-Path $OutputDir "$baseName.txt"

    Write-Host "Processing: $($file.Name)..."

    try {
        # docx files are ZIP archives containing XML
        Add-Type -AssemblyName System.IO.Compression.FileSystem

        $zip = [System.IO.Compression.ZipFile]::OpenRead($file.FullName)
        $documentEntry = $zip.Entries | Where-Object { $_.FullName -eq "word/document.xml" }

        if ($documentEntry) {
            $stream = $documentEntry.Open()
            $reader = New-Object System.IO.StreamReader($stream)
            $xmlContent = $reader.ReadToEnd()
            $reader.Close()
            $stream.Close()

            # Parse XML
            $xml = [xml]$xmlContent
            $nsManager = New-Object System.Xml.XmlNamespaceManager($xml.NameTable)
            $nsManager.AddNamespace("w", "http://schemas.openxmlformats.org/wordprocessingml/2006/main")

            # Extract text from paragraphs
            $paragraphs = $xml.SelectNodes("//w:p", $nsManager)
            $lines = @()

            foreach ($para in $paragraphs) {
                $texts = $para.SelectNodes(".//w:t", $nsManager)
                $lineText = ""
                foreach ($t in $texts) {
                    $lineText += $t.InnerText
                }
                $lineText = $lineText.Trim()
                if ($lineText -ne "") {
                    $lines += $lineText
                }
            }

            # Write to output file
            $lines -join "`n" | Out-File -FilePath $outputFile -Encoding UTF8
            Write-Host "  -> $outputFile ($($lines.Count) lines)"
        }

        $zip.Dispose()
    }
    catch {
        Write-Host "  ERROR: $($_.Exception.Message)"
    }
}

Write-Host "`nDone! Extracted $($docxFiles.Count) files to $OutputDir"
