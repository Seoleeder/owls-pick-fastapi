import base64

# 1. 원본 파일 읽기
with open("secrets/owls-pick-vertex-api-key.json", "rb") as original_file:
    encoded_bytes = base64.b64encode(original_file.read())
    encoded_string = encoded_bytes.decode("utf-8")

# 2. 인코딩된 문자열을 새로운 텍스트 파일로 저장
with open("vertex_key_encoded.txt", "w") as encoded_file:
    encoded_file.write(encoded_string)

print("인코딩 완료! vertex_key_encoded.txt 파일을 확인하세요.")