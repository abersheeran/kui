import os


class DuplicatePathError(Exception):
    pass


class Parser:
    def __init__(self, path):
        self.tree = {}
        self.path = path
        self.rebuild()

    def rebuild(self):
        self.tree = {}
        self._build_tree(self.tree, self.path)

    def _build_tree(self, head: dict, path: str):
        for child in os.listdir(path):
            # Ignore Hidden Path
            if child[:2] == child[-2:] == '__':
                continue

            child_path = os.path.join(path, child)
            if os.path.isfile(child_path):
                child = child[:-3]

            param = None
            if child[0] == '[' and child[-1] == ']':
                param = child[1:-1]
                child = '[]'
            if child in head:
                raise DuplicatePathError('Path {} already exists'.format(child_path[:-3]))

            if os.path.isfile(child_path):
                head[child] = dict(type='module', file=child_path, param=param, name=child)
            else:
                children = dict()
                self._build_tree(children, child_path)
                head[child] = dict(type='path', children=children, param=param, name=child)

    def match_path(self, path: str):
        paths = path.replace('-', '_').split('/')
        if paths[-1] == '':
            paths[-1] = 'index'

        return self._math_node(self.tree, paths, dict())

    def _math_node(self, head, paths: [str], params: dict):
        if len(paths) == 0:
            return None

        curr_match = paths[0]
        paths = paths[1:] if len(paths) > 0 else []

        # The first one or sth like /abd//bcd
        if curr_match == '':
            return self._math_node(head, paths, params)

        # Prior to use Exact Match
        is_exact_match = curr_match in head
        can_wild_match = '[]' in head

        # Match Nothing
        if not is_exact_match and not can_wild_match:
            return None
        curr = head[curr_match if is_exact_match else '[]']

        # If no more child path but it is matching exacting Directory, we will try to match wild_card
        if len(paths) == 0 and can_wild_match and is_exact_match and curr['type'] == 'path':
            curr = head['[]']

        if curr['type'] == 'path':
            curr = curr['children']
            if curr_match in head:
                return self._math_node(curr, paths, params)
            elif '[]' in head:  # wildcard
                params[head['[]']['param']] = curr_match
                return self._math_node(curr, paths, params)

        # Only Last One Can be Module
        elif len(paths) == 0 and curr['type'] == 'module':
            if curr['name'] == curr_match:
                return dict(module=curr['file'], params=params)
            elif curr['name'] == '[]':
                params[curr['param']] = curr_match
                return dict(module=curr['file'], params=params)
        else:
            return None


if __name__ == '__main__':
    parser = Parser('views')
    print(parser.tree)
    print(parser.match_path('/index'))
    print(parser.match_path('/api/index'))
    print(parser.match_path('/api/TEST_ID/test1'))
    print(parser.match_path('/api/TEST_ID/TEST_NAME/'))
    print(parser.match_path('/api/TEST_ID/test/index'))
    print(parser.match_path('/api/TEST_ID/test/name/test'))
    print(parser.match_path('/api/TEST_ID/test/TEST_NAME'))
    print(parser.match_path('/api/TEST_ID/test/name/'))
