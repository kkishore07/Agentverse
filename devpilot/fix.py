import glob

files = glob.glob('tui/**/*.py', recursive=True)
count = 0
for f in files:
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    
    if '$text;' in content or '$text"' in content or "$text'" in content or '$text\n' in content:
        content = content.replace('$text;', '$foreground 50%;')
        content = content.replace('"$text"', '"$foreground 50%"')
        content = content.replace("'$text'", "'$foreground 50%'")
        content = content.replace('$text\n', '$foreground 50%\n')
        
        with open(f, 'w', encoding='utf-8') as file:
            file.write(content)
        count += 1
        print('Updated ' + f)

print('Total files updated:', count)
