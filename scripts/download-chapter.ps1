param(
    [Parameter(Mandatory = $true)]
    [Uri]$ChapterUrl,

    [Parameter(Mandatory = $false)]
    [int]$StartChapter = 265,

    [Parameter(Mandatory = $false)]
    [Nullable[int]]$EndChapter,

    [Parameter(Mandatory = $false)]
    [string]$OutputDirectory = (Join-Path $PSScriptRoot "..\chapters_en")
)

$ErrorActionPreference = "Stop"

if ($ChapterUrl.Host -notin @("vortexscans.org", "www.vortexscans.org")) {
    throw "Pour éviter de télécharger un site inattendu, l'URL doit pointer vers vortexscans.org."
}

if ($ChapterUrl.AbsolutePath -notmatch "/chapter-\d+/?$") {
    throw "L'URL doit se terminer par /chapter-N, par exemple /chapter-240."
}

if ($StartChapter -lt 1) {
    throw "StartChapter doit être supérieur ou égal à 1."
}

if ($EndChapter.HasValue -and $EndChapter.Value -lt $StartChapter) {
    throw "EndChapter doit être supérieur ou égal à StartChapter."
}

New-Item -ItemType Directory -Path $OutputDirectory -Force | Out-Null

$headers = @{
    "User-Agent" = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131 Safari/537.36"
}

$chapterUrlPattern = $ChapterUrl.AbsoluteUri -replace "chapter-\d+(?=/?$)", "chapter-{0}"
$chapterNumber = $StartChapter

while ($true) {
    if ($EndChapter.HasValue -and $chapterNumber -gt $EndChapter.Value) {
        break
    }

    $currentChapterUrl = [Uri]::new(($chapterUrlPattern -f $chapterNumber))
    $chapterDirectory = Join-Path $OutputDirectory ("chapter-{0}" -f $chapterNumber)

    try {
        $page = Invoke-WebRequest -Uri $currentChapterUrl -Headers $headers
    }
    catch [System.Net.WebException] {
        $statusCode = $_.Exception.Response.StatusCode.value__
        if (-not $EndChapter.HasValue -and $statusCode -eq 404) {
            Write-Host "Fin de la série détectée au chapitre $($chapterNumber - 1)."
            break
        }

        throw "Impossible de charger le chapitre $chapterNumber (HTTP $statusCode)."
    }

    $imageUrls = [Regex]::Matches(
        $page.Content,
        '<img\b[^>]*\bsrc=["''](?<url>[^"'']+)["''][^>]*>',
        [Text.RegularExpressions.RegexOptions]::IgnoreCase
    ) |
        ForEach-Object { $_.Groups["url"].Value } |
        Where-Object { $_ -match "/upload/series/" } |
        Select-Object -Unique

    if (-not $imageUrls) {
        if (-not $EndChapter.HasValue) {
            Write-Host "Aucune image trouvée au chapitre $chapterNumber : arrêt."
            break
        }

        throw "Aucune image de chapitre n'a été trouvée pour le chapitre $chapterNumber."
    }

    New-Item -ItemType Directory -Path $chapterDirectory -Force | Out-Null

    for ($index = 0; $index -lt $imageUrls.Count; $index++) {
        $imageUrl = [Uri]::new($currentChapterUrl, $imageUrls[$index])
        $extension = [IO.Path]::GetExtension($imageUrl.AbsolutePath)
        if ([string]::IsNullOrWhiteSpace($extension)) {
            $extension = ".webp"
        }

        $filePath = Join-Path $chapterDirectory ("{0:D3}{1}" -f ($index + 1), $extension)
        if (Test-Path -LiteralPath $filePath) {
            Write-Host "Déjà présent: $filePath"
            continue
        }

        Write-Host ("Chapitre {0} - image {1}/{2}" -f $chapterNumber, ($index + 1), $imageUrls.Count)
        Invoke-WebRequest -Uri $imageUrl -Headers $headers -OutFile $filePath
    }

    Write-Host "Chapitre $chapterNumber terminé: $($imageUrls.Count) image(s)."
    $chapterNumber++
}

Write-Host "Téléchargement terminé."
