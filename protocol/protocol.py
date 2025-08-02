# so encoding it receives key value pairs, then for each key value pair it joins them with \n at the end \n\n  
# examaple TYPE:POST\nMESSAGE:"hello"\n\n
class Protocol(object):
    def encode_message(data: dict) -> bytes:
        return ('\n'.join(f"{k}:{v}" for k, v in data.items()) + '\n\n').encode('utf-8')
    # when decoding for every split with \n it further splits each pair using ':' then returns it
    
    def decode_message(message:bytes)-> dict:
        text = message.decode('utf-8')
        pairs = (item.split(':', 1) for item in text.split('\n') if ':' in item)
        return {k: v for k, v in pairs}