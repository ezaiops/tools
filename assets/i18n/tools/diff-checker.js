/* Diff checker page dictionary. */
window.I18N_DICTS = window.I18N_DICTS || [];
window.I18N_DICTS.push({
  "Text diff checker": "文本差异对比",
  "Paste two versions of a text and see exactly what changed — line by line, with changed words highlighted inside modified lines. A compact Myers diff runs locally; nothing is uploaded.": "粘贴两段文本，看清到底改了什么——逐行对比，修改行内的变化单词会高亮。紧凑的 Myers diff 在本地运行；不上传任何内容。",
  "Diff checker": "差异对比",
  "Original": "原文",
  "Modified": "修改后",
  "Compare": "对比",
  "Swap sides": "交换两侧",
  "Highlight changed words": "高亮变化的单词",
  "Lines added": "新增行",
  "Lines removed": "删除行",
  "Lines changed": "修改行",
  "Lines total": "总行数",
  "How the diff works": "差异是怎么算的",
  "Line differences come from the Myers O(ND) algorithm — the same family that powers git diff. It finds the shortest edit script (insertions and deletions) between the two line sequences. Modified lines are then paired up and a word-level Myers pass highlights the changed words inside them, which is what makes small edits readable at a glance.": "行级差异来自 Myers O(ND) 算法——与 git diff 同族。它找出两行序列之间的最短编辑脚本（插入和删除）。修改行会被配对，再用一次词级 Myers 过程高亮其中变化的单词，这正是小改动一目了然的原因。",
  "Everything runs in JavaScript on your device. For larger inputs the algorithm is linear-ish in practice but quadratic in the worst case — pasting a few thousand lines is fine; pasting a whole codebase is not.": "一切都在你设备的 JavaScript 中运行。实际表现接近线性，最坏情况是平方级——粘贴几千行没问题，粘贴整个代码库就不行了。",
  "How is this different from git diff?": "这和 git diff 有什么区别？",
  "Same line-diff algorithm, but git also applies heuristics (hunk headers, function context, whitespace rules). For comparing two arbitrary text blobs — emails, config files, drafts — this is faster to reach for.": "行级算法相同，但 git 还会应用启发式规则（差异块头、函数上下文、空白处理）。比较两个任意文本块——邮件、配置文件、草稿——这个工具更快。",
  "Does it ignore whitespace?": "会忽略空白吗？",
  "No — a trailing space is a difference. Trim both sides first if you want whitespace-insensitive comparison.": "不会——行尾空格也算差异。想要忽略空白的比较，先自行去除两侧空白。",
  "Is my text uploaded?": "文本会被上传吗？",
  "No. The diff is computed in your browser; the page never transmits the contents.": "不会。差异在你的浏览器中计算，页面从不传输内容。"
});
