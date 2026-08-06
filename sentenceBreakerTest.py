from sentence_breaker import segment_text

text = ""
while(text != "exit"):
 text = input()
 segments = segment_text(text)
 print(segments)