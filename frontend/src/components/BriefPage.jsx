function inline(text) {
  const parts = [];
  const re = /\*\*(.+?)\*\*/g;
  let last = 0;
  let match;
  while ((match = re.exec(text))) {
    if (match.index > last) parts.push(text.slice(last, match.index));
    parts.push(
      <strong key={match.index} className="font-bold">
        {match[1]}
      </strong>,
    );
    last = match.index + match[0].length;
  }
  if (last < text.length) parts.push(text.slice(last));
  return parts.length ? parts : text;
}

function parse(markdown) {
  const nodes = [];
  let list = [];

  function flush() {
    if (!list.length) return;
    nodes.push({ type: "ul", items: list });
    list = [];
  }

  for (const raw of markdown.split("\n")) {
    const line = raw.replace(/\s+$/, "");
    if (line.startsWith("# ")) {
      flush();
      nodes.push({ type: "h1", text: line.slice(2) });
    } else if (line.startsWith("## ")) {
      flush();
      nodes.push({ type: "h2", text: line.slice(3) });
    } else if (line.startsWith("- ") || line.startsWith("  - ")) {
      list.push(line.replace(/^\s*-\s*/, ""));
    } else if (!line.trim()) {
      flush();
    } else {
      flush();
      nodes.push({ type: "p", text: line });
    }
  }
  flush();
  return nodes;
}

export function BriefPage({ markdown }) {
  if (!markdown) return null;

  return (
    <article className="brief-page nhs-card p-5">
      {parse(markdown).map((node, i) => {
        if (node.type === "h1") return <h1 key={i}>{inline(node.text)}</h1>;
        if (node.type === "h2") return <h2 key={i}>{inline(node.text)}</h2>;
        if (node.type === "p") return <p key={i}>{inline(node.text)}</p>;
        return (
          <ul key={i}>
            {node.items.map((item, j) => (
              <li key={j}>{inline(item)}</li>
            ))}
          </ul>
        );
      })}
    </article>
  );
}
