def deserialize_xml(xml_text):
    pos = [0, 1]
    length = len(xml_text)

    def get_char():
        return xml_text[pos[0]] if pos[0] < length else None

    def advance():
        if get_char() == '\n':
            pos[1] += 1
        pos[0] += 1

    def skip_whitespace():
        while pos[0] < length and get_char() in (' ', '\t', '\n', '\r'):
            advance()

    def error(msg):
        raise ValueError(f"{msg} на строке {pos[1]}")

    def parse_name():
        start = pos[0]
        while pos[0] < length and get_char() and (get_char().isalnum() or get_char() in '-_.:'):
            advance()
        name = xml_text[start:pos[0]]
        if not name:
            error("Ожидается имя тега")
        return name

    def parse_attr_value():
        if get_char() != '"':
            error("Ожидается \"")
        advance()
        res = []
        while pos[0] < length and get_char() != '"':
            res.append(get_char())
            advance()
        if get_char() != '"':
            error("Незакрытый атрибут")
        advance()
        return "".join(res)

    def parse_attributes():
        attrs = {}
        while pos[0] < length:
            skip_whitespace()
            c = get_char()
            if c in ('>', '/', None):
                break
            name = parse_name()
            skip_whitespace()
            if get_char() != '=':
                error("Ожидается =")
            advance()
            skip_whitespace()
            attrs[name] = parse_attr_value()
        return attrs

    def parse_content(tag_name):
        children = []
        text_buffer = []

        while pos[0] < length:
            closing_tag = f'</{tag_name}>'
            if xml_text.startswith(closing_tag, pos[0]):
                pos[0] += len(closing_tag)
                break

            if get_char() == '<':
                txt = "".join(text_buffer).strip()
                if txt:
                    children.append({"type": "text", "content": txt})
                text_buffer = []
                children.append(parse_node())
            else:
                text_buffer.append(get_char())
                advance()

        txt = "".join(text_buffer).strip()
        if txt:
            children.append({"type": "text", "content": txt})
        return children

    def parse_node():
        if get_char() != '<':
            error("Ожидается <")
        advance()
        if get_char() == '/':
            error("Неожиданный закрывающий тег")
        if get_char() == '!':
            error("Комментарии не поддерживаются")

        tag_name = parse_name()
        attrs = parse_attributes()

        if get_char() == '/':
            advance()
            if get_char() != '>':
                error("Ожидается >")
            advance()
            return {"tag": tag_name, "attrs": attrs, "children": [], "text": None}

        if get_char() != '>':
            error("Ожидается >")
        advance()

        content = parse_content(tag_name)
        node = {"tag": tag_name, "attrs": attrs, "children": [], "text": None}
        for item in content:
            if item.get("type") == "text":
                node["text"] = item["content"]
            else:
                node["children"].append(item)
        return node

    skip_whitespace()
    root = parse_node()
    skip_whitespace()
    if pos[0] < length:
        error("Данные после корневого элемента")
    return root


def validate_xml(xml_text):
    try:
        deserialize_xml(xml_text)
        return True, None
    except ValueError as err:
        msg = str(err)
        if "на строке" in msg:
            line = int(msg.split("на строке ")[1])
            return False, line
        return False, 1


def build_xml_string(node, indent_level, indent_step, compact):
    tag = node["tag"]
    attrs = node.get("attrs", {})
    children = node.get("children", [])
    text = node.get("text")

    attr_str = "".join(f' {k}="{v}"' for k, v in attrs.items())
    pad = " " * indent_level
    next_pad = " " * (indent_level + indent_step)
    nl = "" if compact else "\n"
    sp = "" if compact else " "

    has_content = bool(children) or (text and text.strip())
    if not has_content:
        return f"{pad}<{tag}{attr_str}/>{nl}"

    res = f"{pad}<{tag}{attr_str}>{nl}"
    if text:
        res += (next_pad if not compact else "") + text.strip() + nl
    for child in children:
        if child.get("type") == "text":
            res += (next_pad if not compact else "") + child["content"].strip() + nl
        else:
            res += build_xml_string(child, indent_level + indent_step, indent_step, compact)

    res += f"{pad}</{tag}>{nl}"
    return res


def serialize_xml(xml_dict):
    return build_xml_string(xml_dict, 0, 0, compact=True)


def format_xml_indent(xml_dict, indent_size):
    return build_xml_string(xml_dict, 0, indent_size, compact=False)


sample_xml = """<iotNetwork id="net-001" location="Factory A">
    <device id="dev-1001" type="temperature_sensor" status="online">
        <firmware version="1.2.3" lastUpdate="2026-04-01T10:00:00Z"/>

        <metrics>
            <entry timestamp="2026-04-05T10:00:00Z">
                <temperature>22.5</temperature>
                <humidity>45.2</humidity>
            </entry>
            <entry timestamp="2026-04-05T10:05:00Z">
                <temperature>22.8</temperature>
                <humidity>44.9</humidity>
            </entry>
        </metrics>

        <alerts>
            <alert type="threshold" severity="warning">
                Temperature approaching limit
            </alert>
        </alerts>
    </device>
</iotNetwork>"""

print("1. Десериализация (Python-дерево):")
tree = deserialize_xml(sample_xml)
print(tree)

print("\n2. Валидация исходного XML:")
is_valid, err_line = validate_xml(sample_xml)
print(f"Валиден: {is_valid}, строка ошибки: {err_line}")

print("\n3. Сериализация (компактно):")
compact_xml = serialize_xml(tree)
print(compact_xml)

print("\n4. Вывод с отступами (4):")
pretty_xml = format_xml_indent(tree, indent_size=4)
print(pretty_xml)

broken_xml = "<root><child>test</chlid></root>"
print("\n5. Валидация сломанного XML:")
is_valid, err_line = validate_xml(broken_xml)
print(f"Валиден: {is_valid}, строка ошибки: {err_line}")