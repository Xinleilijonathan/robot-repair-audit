# Locate the agent CLIs installed from inside the Claude app (its AppData writes are redirected).
Get-ChildItem 'C:\Users\Jonat\AppData\Local\Packages' -Directory -Filter 'Claude*' | ForEach-Object {
    $root = Join-Path $_.FullName 'LocalCache\Roaming\npm\node_modules'
    'package: ' + $_.FullName
    foreach ($rel in '@anthropic-ai\claude-code\bin\claude.exe', '@google\gemini-cli\bundle\gemini.js', '@openai\codex\bin\codex.js') {
        $p = Join-Path $root $rel
        '  ' + $rel + ' -> ' + (Test-Path $p)
    }
}
'real npm: ' + (Test-Path 'C:\Users\Jonat\AppData\Roaming\npm\node_modules')
