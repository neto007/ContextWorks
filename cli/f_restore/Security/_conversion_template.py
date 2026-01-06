"""
Template para conversão de ferramentas de path para file_content

Ferramentas identificadas para conversão:
1. quark.py - apk_path -> file_content
2. droidefense.py - apk_path -> file_content  
3. apkhunt.py - apk_path -> file_content
4. adhrit.py - apk_path -> file_content
5. androwarn.py - apk_path -> file_content
6. apkleaks.py - apk_file_path -> file_content
7. app_info_scanner.py - app_path -> file_content
8. droidlysis.py - apk_path -> file_content
9. rz_ghidra.py - binary_path -> file_content
10. cwe_checker.py - binary_path -> file_content
11. habo.py - binary_path -> file_content
12. qiling.py - binary_path -> file_content
13. dorothy2.py - binary_path -> file_content
14. bincat.py - binary_path -> file_content
15. binwalk.py - file_path -> file_content
16. angr.py - binary_path -> file_content
17. binabs.py - binary_path -> file_content

Padrão de conversão:
- Adicionar: import tempfile, base64
- Mudar parâmetro: path: str -> file_content: bytes, filename: str
- Criar tempfile.TemporaryDirectory()
- Escrever file_content no arquivo temporário
- Montar o tmpdir no Docker
"""
