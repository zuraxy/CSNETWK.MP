# so encoding it receives key value pairs, then for each key value pair it joins them with \n at the end \n\n  
# examaple TYPE:POST\nMESSAGE:"hello"\n\n

# Example input message
# original message = {
# "TYPE": "POST",
# "USER_ID": "john_doe",
# "CONTENT": "f83d2b1c"
# }

class Protocol(object):
    def encode_message(data: dict) -> bytes:
        return ('\n'.join(f"{k}:{v}" for k, v in data.items()) + '\n\n').encode('utf-8')
    # when decoding for every split with \n it further splits each pair using ':' then returns it

    # example original message earlier upon being encoded results to:
    # b'TYPE:POST\nUSER_ID:john_doe\nCONTENT:f83d2b1c\n\n' 
    # b'<value>' means byte of <value>
    
    def decode_message(message:bytes)-> dict:
        text = message.decode('utf-8')
        pairs = (item.split(':', 1) for item in text.split('\n') if ':' in item)
        return {k: v for k, v in pairs}
    
    # Example original message earlier decoded outputs a dictionary. This works by converting the bytes back to a UTF-8 string first, split string by newlines, then for each line containing a colon, split at first colon to create the key-value pairs then build and return a dictionary from those pairs
    # Output:
    # {
    # 'TYPE': 'POST',
    # 'USER_ID': 'john_doe',
    # 'CONTENT': 'f83d2b1c'
    # }