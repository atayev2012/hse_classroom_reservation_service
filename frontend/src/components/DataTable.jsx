export default function DataTable({ columns, rows, mutedRows = [] }) {
  return (
    <div className="data-table">
      <div className="data-table__head" style={{ gridTemplateColumns: columns.map((col) => col.width || '1fr').join(' ') }}>
        {columns.map((col) => (
          <div key={col.key}>{col.label}</div>
        ))}
      </div>
      {rows.map((row, index) => (
        <div
          className={`data-table__row ${mutedRows.includes(index) ? 'is-muted' : ''}`}
          style={{ gridTemplateColumns: columns.map((col) => col.width || '1fr').join(' ') }}
          key={row.id || index}
        >
          {columns.map((col) => (
            <div key={col.key} className={col.className ? col.className(row) : ''}>
              {col.render ? col.render(row, index) : row[col.key]}
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}
