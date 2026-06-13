import re


class Searcher:
    def __init__(self, apps):
        self.apps = apps

    def search(self, query, max_results=10):
        normalized_query = self._normalize(query)
        if not normalized_query:
            return self.apps[:max_results]

        results = []
        for app in self.apps:
            score = self._score_app(app, normalized_query)
            if score is not None:
                results.append({"app": app, "score": score})

        results.sort(key=lambda item: item["score"])
        return [item["app"] for item in results[:max_results]]

    def _score_app(self, app, query):
        name = app["name"].lower()
        path = app["path"].lower()
        normalized_name = self._normalize(name)
        normalized_path = self._normalize(path)

        score = 0

        if query in normalized_name:
            score -= 12
            if normalized_name.startswith(query):
                score -= 6
        elif query in normalized_path:
            score -= 5

        if self._contains_all_characters(query, normalized_name):
            score -= 4

        if self._is_subsequence(query, normalized_name):
            score -= 3

        abbreviation = self._build_abbreviation(name, path)
        if query in abbreviation:
            score -= 8
            if abbreviation.startswith(query):
                score -= 2

        if score >= 0:
            return None

        # Prefer shorter names when scores tie so the top matches feel tighter.
        return score, len(name), name

    def _normalize(self, value):
        return re.sub(r"[^0-9a-z\u4e00-\u9fff]+", "", value.lower().strip())

    def _contains_all_characters(self, query, name):
        return all(char in name for char in query)

    def _is_subsequence(self, query, target):
        if not query:
            return False

        query_index = 0
        for char in target:
            if char == query[query_index]:
                query_index += 1
                if query_index == len(query):
                    return True
        return False

    def _build_abbreviation(self, name, path):
        tokens = re.split(r"[^0-9A-Za-z\u4e00-\u9fff]+", f"{name} {path}")
        initials = []

        for token in tokens:
            if not token:
                continue

            if self._contains_cjk(token):
                initials.extend(self._get_pinyin_initial(char) for char in token if "\u4e00" <= char <= "\u9fff")
                continue

            initials.append(token[0].lower())

        return "".join(initials)

    def _contains_cjk(self, text):
        return any("\u4e00" <= char <= "\u9fff" for char in text)

    def _get_pinyin_initial(self, char):
        if not ("\u4e00" <= char <= "\u9fff"):
            return char.lower()

        try:
            gbk_bytes = char.encode("gbk")
        except UnicodeEncodeError:
            return char.lower()

        if len(gbk_bytes) < 2:
            return char.lower()

        code = gbk_bytes[0] * 256 + gbk_bytes[1] - 65536
        ranges = (
            (-20319, "a"),
            (-20284, "b"),
            (-19776, "c"),
            (-19219, "d"),
            (-18711, "e"),
            (-18527, "f"),
            (-18240, "g"),
            (-17923, "h"),
            (-17418, "j"),
            (-16475, "k"),
            (-16213, "l"),
            (-15641, "m"),
            (-15166, "n"),
            (-14923, "o"),
            (-14915, "p"),
            (-14631, "q"),
            (-14150, "r"),
            (-14091, "s"),
            (-13319, "t"),
            (-12839, "w"),
            (-12557, "x"),
            (-11848, "y"),
            (-11056, "z"),
        )

        initial = char.lower()
        for boundary, letter in ranges:
            if code < boundary:
                break
            initial = letter

        return initial
