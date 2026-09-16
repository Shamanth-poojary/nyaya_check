import re

with open('src/app/page.tsx', 'r', encoding='utf-8') as f:
    code = f.read()

# Fix boolean HTML attributes
code = code.replace('required=""', 'required')
code = code.replace('disabled=""', 'disabled')
code = code.replace('readonly=""', 'readOnly')

with open('src/app/page.tsx', 'w', encoding='utf-8') as f:
    f.write(code)

print('Fixed JSX boolean attributes in src/app/page.tsx')
