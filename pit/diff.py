from dataclasses import dataclass

from pit.constants import Color


@dataclass
class Edit:
    TYPE_COLORS = {
        '-': Color.RED,
        '+': Color.GREEN,
        ' ': ''
    }
    type: str
    text: str | bytes

    def __str__(self):
        return f"{self.TYPE_COLORS[self.type]}{self.type} {self.text if isinstance(self.text, str) else self.text.decode()}{Color.RESET_ALL}"


class Diff:
    def __init__(self, a: str | bytes | list, b: str | bytes | list):
        self.a = a
        self.b = b

    def diff(self):
        diff = []
        for ((prev_x, prev_y), (x, y)) in self.backtrack():
            if prev_x == x:
                diff.append(Edit("+", self.b[prev_y]))
            elif prev_y == y:
                diff.append(Edit("-", self.a[prev_x]))
            else:
                diff.append(Edit(" ", self.a[prev_x]))
        diff.reverse()
        return diff

    def shortest_edit(self):
        n, m = len(self.a), len(self.b)
        max_ = n + m
        v: list[int | None] = [None] * (2 * max_ + 1)
        v[1] = 0

        trace = []
        for d in range(max_ + 1):
            trace.append(v.copy())
            for k in range(-d, d + 1, 2):
                # k 为 -d 时，表明一直沿着 y 轴向下移动，
                # 又因为 k = x - y，所以 x 不变，y + 1 导致 k_end = x - (y + 1) =  k_start - 1
                # => k_start = k_end + 1 => x_end = x_start = v[k_end + 1]
                if k == -d:
                    x = v[k + 1]
                # k 为 d 时，表明一直沿着 x 轴向右移动，
                # 又因为 k = x - y，所以 x + 1，y 不变 导致 k_end = x + 1 - y =  k_start + 1
                # => k_start = k_end - 1 => x_end = x_start + 1 = v[k_start] + 1 = v[k_end - 1] + 1
                elif k == d:
                    x = v[k - 1] + 1
                # k 处于 -d 和 d 中间时，表明当前位置可能由原有位置右移（删除）或下移（增加）而来，
                # 又因为我们优先删除，所以当可能右移的位置的 x 值 >= 可能下移的位置时，果断选择右移
                # 除非选择下移的位置的 x 值小于右移的 x 值，可以补偿一次下移的损失
                elif v[k - 1] >= v[k + 1]:
                    x = v[k - 1] + 1
                else:
                    x = v[k + 1]
                # 合并上面的表达式可以简化为
                # if k == -d or (k != d and v[k - 1] < v[k + 1]):
                #     x = v[k + 1]
                # else:
                #     x = v[k - 1] + 1

                y = x - k
                # 处理字符相同，可以跳过图中对角线的情况
                while x < n and y < m and self.a[x] == self.b[y]:
                    x, y = x + 1, y + 1
                v[k] = x

                if x >= n and y >= m:
                    return trace

    def backtrack(self):
        x, y = len(self.a), len(self.b)
        for d, v in reversed(list(enumerate(self.shortest_edit()))):
            k = x - y

            if k == -d or (k != d and v[k - 1] < v[k + 1]):
                prev_k = k + 1
            else:
                prev_k = k - 1

            prev_x = v[prev_k]
            prev_y = prev_x - prev_k

            while x > prev_x and y > prev_y:
                yield (x - 1, y - 1), (x, y)
                x, y = x - 1, y - 1

            if d > 0:
                yield (prev_x, prev_y), (x, y)
            x, y = prev_x, prev_y


if __name__ == "__main__":
    for edit in Diff("ABCABBA", "CBABAC").diff():
        print(edit)

"""
- A
- B
  C
+ B
  A
  B
- B
  A
+ C
"""
