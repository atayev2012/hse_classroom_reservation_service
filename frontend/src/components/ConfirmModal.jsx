export default function ConfirmModal({
  title = 'Подтверждение',
  message = 'Вы уверены?',
  confirmLabel = 'Да',
  cancelLabel = 'Нет',
  onConfirm,
  onCancel
}) {
  return (
    <div className="modal-backdrop">
      <div className="user-modal confirm-modal">
        <h2>{title}</h2>
        <p>{message}</p>
        <div className="modal-actions">
          <button className="button button--danger" type="button" onClick={onCancel}>
            {cancelLabel}
          </button>
          <button className="button button--primary" type="button" onClick={onConfirm}>
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
