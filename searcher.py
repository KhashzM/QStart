import re

class Searcher:
    def __init__(self, apps):
        self.apps = apps
    
    def search(self, query, max_results=10):
        if not query:
            return self.apps[:max_results]
        
        query = query.lower().strip()
        results = []
        
        for app in self.apps:
            name = app["name"].lower()
            path = app["path"].lower()
            
            score = 0
            
            if query in name:
                score -= 10
                pos = name.find(query)
                if pos == 0:
                    score -= 5
            elif query in path:
                score -= 5
            
            if self._match_chinese_characters(query, name):
                score -= 3
            
            if self._contains_all_characters(query, name):
                score -= 4
            
            if self._match_abbreviation(query, name):
                score -= 8
            
            if score < 0:
                results.append({
                    "app": app,
                    "score": score
                })
        
        results.sort(key=lambda x: x["score"])
        
        return [r["app"] for r in results[:max_results]]
    
    def _match_chinese_characters(self, query, name):
        query_chars = set(query)
        name_chars = set(name)
        matched = query_chars.intersection(name_chars)
        return len(matched) >= len(query_chars) * 0.7
    
    def _contains_all_characters(self, query, name):
        for char in query:
            if char not in name:
                return False
        return True
    
    def _match_abbreviation(self, query, name):
        if len(query) <= 1:
            return False
        
        initials = []
        for char in name:
            if '\u4e00' <= char <= '\u9fff':
                initial = self._get_pinyin_initial(char)
                if initial:
                    initials.append(initial)
            else:
                initials.append(char.lower())
        
        initials_str = ''.join(initials)
        return query.lower() in initials_str
    
    def _get_pinyin_initial(self, char):
        pinyin_map = {
            'a': '\u554a\u963f\u9515\u535c\u840c\u62c9\u535a\u5bb6\u8774\u7b14\u590d\u8f66',
            'b': '\u535c\u840c\u62c9\u535a\u5bb6\u8774\u7b14\u590d\u8f66\u884c\u643a\u914d',
            'c': '\u4e09\u4e00\u4e2d\u660e\u5916\u6c11\u6e05\u53e3\u4ec1\u53ca\u56fd\u66fc',
            'd': '\u56db\u4e8c\u7b2c\u7684\u5f00\u59cb\u90fd\u5728\u8fd9\u91cc\u548c\u90a3\u91cc',
            'e': '\u4e8c\u4e00\u4e2d\u7684\u4e8c\u662f\u8fd9\u4e2a\u4e8c',
            'f': '\u4e09\u4e2d\u7684\u4e09\u662f\u8fd9\u4e2a\u4e09',
            'g': '\u56db\u4e2d\u7684\u56db\u662f\u8fd9\u4e2a\u56db',
            'h': '\u4e94\u4e2d\u7684\u4e94\u662f\u8fd9\u4e2a\u4e94',
            'j': '\u516d\u4e2d\u7684\u516d\u662f\u8fd9\u4e2a\u516d',
            'k': '\u4e03\u4e2d\u7684\u4e03\u662f\u8fd9\u4e2a\u4e03',
            'l': '\u516b\u4e2d\u7684\u516b\u662f\u8fd9\u4e2a\u516b',
            'm': '\u4e5d\u4e2d\u7684\u4e5d\u662f\u8fd9\u4e2a\u4e5d',
            'n': '\u5341\u4e2d\u7684\u5341\u662f\u8fd9\u4e2a\u5341',
            'o': '\u5341\u4e00\u4e2d\u7684\u5341\u4e00\u662f\u8fd9\u4e2a\u5341\u4e00',
            'p': '\u5341\u4e8c\u4e2d\u7684\u5341\u4e8c\u662f\u8fd9\u4e2a\u5341\u4e8c',
            'q': '\u5341\u4e09\u4e2d\u7684\u5341\u4e09\u662f\u8fd9\u4e2a\u5341\u4e09',
            'r': '\u5341\u56db\u4e2d\u7684\u5341\u56db\u662f\u8fd9\u4e2a\u5341\u56db',
            's': '\u5341\u4e94\u4e2d\u7684\u5341\u4e94\u662f\u8fd9\u4e2a\u5341\u4e94',
            't': '\u5341\u516d\u4e2d\u7684\u5341\u516d\u662f\u8fd9\u4e2a\u5341\u516d',
            'w': '\u5341\u4e03\u4e2d\u7684\u5341\u4e03\u662f\u8fd9\u4e2a\u5341\u4e03',
            'x': '\u5341\u516b\u4e2d\u7684\u5341\u516b\u662f\u8fd9\u4e2a\u5341\u516b',
            'y': '\u5341\u4e5d\u4e2d\u7684\u5341\u4e5d\u662f\u8fd9\u4e2a\u5341\u4e5d',
            'z': '\u4e8c\u5341\u4e2d\u7684\u4e8c\u5341\u662f\u8fd9\u4e2a\u4e8c\u5341',
        }
        
        for initial, chars in pinyin_map.items():
            if char in chars:
                return initial
        return None