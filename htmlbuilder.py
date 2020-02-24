class Element:
    __slots__ = ('attributes', 'children')
    name = 'element'
    def __init__(self, *args, **kwargs):
        self.attributes = {k.replace('_', '-'): v for k, v in kwargs.items()}
        self.children = []
        for item in args:
            if type(item) in (list, tuple):
                self.children.extend(item)
            elif isinstance(item, dict):
                self.attributes.update(item)
            elif isinstance(item, Element):
                self.children.append(item)
            else:
                self.children.append(str(item))

    def __str__(self):
        if self.attributes:
            opener = '<{} {}>'.format(self.name, ' '.join('{}="{}"'.format(key, value) for key, value in self.attributes.items()))
        else:
            opener = '<{}>'.format(self.name)

        closer = '</{0}>'.format(self.name)

        descendants = self.descendants
        if descendants == 0:
            return opener[:-1] + '/>'
        elif descendants == 1:
            return opener + str(self.children[0]) + closer
        else:
            return '{}\n{}\n{}'.format(
                opener,
                indent_string('\n'.join(
                    str(child) for child in self.children
                )),
                closer
            )
    
    @property
    def descendants(self):
        total = 0
        for child in self.children:
            total += 1
            if not isinstance(child, str):
                total += child.descendants
        return total


class Html(Element):
    name = 'html'
    def __str__(self):
        return '<!DOCTYPE html>\n' + super().__str__()


class A(Element):
    name = 'a'


class P(Element):
    name = 'p'
        

class H1(Element):
    name = 'h1'


class H2(Element):
    name = 'h2'


class H3(Element):
    name = 'h3'


class H4(Element):
    name = 'h4'


class H5(Element):
    name = 'h5'


class H6(Element):
    name = 'h6'


class Br(Element):
    name = 'br'


class Tr(Element):
    name = 'tr'


class Th(Element):
    name = 'th'


class Td(Element):
    name = 'td'


class Table(Element):
    name = 'table'


class Head(Element):
    name = 'head'


class Body(Element):
    name = 'body'


class Div(Element):
    name = 'div'


class Span(Element):
    name = 'span'


class Meta(Element):
    name = 'meta'


class Title(Element):
    name = 'title'


class Link(Element):
    name = 'link'


class Script(Element):
    name = 'script'


def indent_string(s, level=1):
    indent = '    '*level
    return indent + s.replace('\n', '\n' + indent)
