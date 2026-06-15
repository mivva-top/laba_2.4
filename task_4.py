def deserialize_json(json_text):
    state = [0, 1]
    text_length = len(json_text)

    def get_char():
        if state[0] < text_length:
            return json_text[state[0]]
        return None

    def advance():
        if get_char() == '\n':
            state[1] += 1
        state[0] += 1

    def skip_whitespace():
        while state[0] < text_length and get_char() in (' ', '\t', '\n', '\r'):
            advance()

    def raise_err(msg):
        raise ValueError(f"{msg} на строке {state[1]}")

    def parse_string():
        if get_char() != '"':
            raise_err("Ожидается '\"'")
        advance()
        chars = []
        while True:
            c = get_char()
            if c == '"':
                advance()
                return "".join(chars)
            if c == '\\':
                advance()
                nxt = get_char()
                if nxt == '"':
                    chars.append('"')
                elif nxt == '\\':
                    chars.append('\\')
                elif nxt == '/':
                    chars.append('/')
                elif nxt == 'n':
                    chars.append('\n')
                elif nxt == 't':
                    chars.append('\t')
                elif nxt == 'r':
                    chars.append('\r')
                elif nxt == 'b':
                    chars.append('\b')
                elif nxt == 'f':
                    chars.append('\f')
                else:
                    raise_err("Недопустимая экранирующая последовательность")
                advance()
            else:
                chars.append(c)
                advance()

    def parse_number():
        start = state[0]
        if get_char() == '-':
            advance()
        if get_char() == '0':
            advance()
        elif get_char() and get_char() in '123456789':
            while get_char() and get_char() in '0123456789':
                advance()
        else:
            raise_err("Недопустимое число")

        if get_char() == '.':
            advance()
            if not (get_char() and get_char() in '0123456789'):
                raise_err("Недопустимое число")
            while get_char() and get_char() in '0123456789':
                advance()

        if get_char() and get_char() in 'eE':
            advance()
            if get_char() in '+-':
                advance()
            if not (get_char() and get_char() in '0123456789'):
                raise_err("Недопустимое число")
            while get_char() and get_char() in '0123456789':
                advance()

        num_str = json_text[start:state[0]]
        if '.' in num_str or 'e' in num_str or 'E' in num_str:
            return float(num_str)
        return int(num_str)

    def parse_literal():
        if json_text.startswith('true', state[0]):
            state[0] += 4
            return True
        if json_text.startswith('false', state[0]):
            state[0] += 5
            return False
        if json_text.startswith('null', state[0]):
            state[0] += 4
            return None

    def parse_object():
        if get_char() != '{':
            raise_err("Ожидается '{'")
        advance()
        result = {}
        skip_whitespace()
        if get_char() == '}':
            advance()
            return result
        while True:
            skip_whitespace()
            key = parse_string()
            skip_whitespace()
            if get_char() != ':':
                raise_err("Ожидается ':'")
            advance()
            skip_whitespace()
            val = parse_value()
            result[key] = val
            skip_whitespace()
            if get_char() == '}':
                advance()
                return result
            if get_char() == ',':
                advance()
            else:
                raise_err("Ожидается ',' или '}'")

    def parse_array():
        if get_char() != '[':
            raise_err("Ожидается '['")
        advance()
        result = []
        skip_whitespace()
        if get_char() == ']':
            advance()
            return result
        while True:
            skip_whitespace()
            val = parse_value()
            result.append(val)
            skip_whitespace()
            if get_char() == ']':
                advance()
                return result
            if get_char() == ',':
                advance()
            else:
                raise_err("Ожидается ',' или ']'")

    def parse_value():
        c = get_char()
        if c == '{':
            return parse_object()
        if c == '[':
            return parse_array()
        if c == '"':
            return parse_string()
        if c in ('t', 'f', 'n'):
            return parse_literal()
        if c and c in '-0123456789':
            return parse_number()
        raise_err("Неожиданный символ")

    skip_whitespace()
    parsed_data = parse_value()
    skip_whitespace()
    if state[0] < text_length:
        raise_err("Неожиданные символы после JSON")
    return parsed_data


def validate_json(json_text):
    try:
        deserialize_json(json_text)
        return True, None
    except ValueError as err:
        msg = str(err)
        if "на строке" in msg:
            err_line = int(msg.split("на строке ")[1])
            return False, err_line
        return False, 1


def serialize_value(obj, indent_level, indent_step):
    if type(obj) is bool:
        return "true" if obj else "false"
    if obj is None:
        return "null"
    if type(obj) in (int, float):
        return str(obj)
    if type(obj) is str:
        escaped = []
        for c in obj:
            if c == '"':
                escaped.append('\\"')
            elif c == '\\':
                escaped.append('\\\\')
            elif c == '\n':
                escaped.append('\\n')
            elif c == '\t':
                escaped.append('\\t')
            elif c == '\r':
                escaped.append('\\r')
            elif c == '\b':
                escaped.append('\\b')
            elif c == '\f':
                escaped.append('\\f')
            else:
                escaped.append(c)
        return '"' + "".join(escaped) + '"'

    if type(obj) is list:
        if not obj: return "[]"
        if indent_step > 0:
            cur_pad = " " * indent_level
            next_pad = " " * (indent_level + indent_step)
            items = []
            for item in obj:
                items.append(next_pad + serialize_value(item, indent_level + indent_step, indent_step))
            return "[\n" + ",\n".join(items) + "\n" + cur_pad + "]"
        else:
            items = [serialize_value(item, 0, 0) for item in obj]
            return "[" + ", ".join(items) + "]"

    if type(obj) is dict:
        if not obj: return "{}"
        if indent_step > 0:
            cur_pad = " " * indent_level
            next_pad = " " * (indent_level + indent_step)
            items = []
            for key in obj:
                k_str = serialize_value(key, 0, 0)
                v_str = serialize_value(obj[key], indent_level + indent_step, indent_step)
                items.append(next_pad + k_str + ": " + v_str)
            return "{\n" + ",\n".join(items) + "\n" + cur_pad + "}"
        else:
            items = []
            for key in obj:
                k_str = serialize_value(key, 0, 0)
                v_str = serialize_value(obj[key], 0, 0)
                items.append(k_str + ": " + v_str)
            return "{" + ", ".join(items) + "}"

    raise TypeError("Неподдерживаемый тип: " + str(type(obj)))


def serialize_json(obj):
    return serialize_value(obj, indent_level=0, indent_step=0)


def format_json(obj, indent_size):
    return serialize_value(obj, indent_level=0, indent_step=indent_size)


test_data = {
    "name": "Alice",
    "age": 25,
    "isStudent": False
}

json_str = serialize_json(test_data)
print("1. Сериализация:")
print(json_str)

pretty_str = format_json(test_data, indent_size=4)
print("\n2. С отступами:")
print(pretty_str)

parsed_data = deserialize_json(json_str)
print("\n3. Десериализация:")
print(parsed_data)

ok, line = validate_json(json_str)
print(f"\n4. Валидация корректного: {ok}, строка ошибки: {line}")

bad_json = '{"name": "Bob", "age": 30, "isStudent": tru}'
ok, line = validate_json(bad_json)
print(f"5. Валидация некорректного: {ok}, строка ошибки: {line}")