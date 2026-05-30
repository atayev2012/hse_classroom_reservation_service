import { ChevronLeft, ChevronRight, Edit3, Plus, Trash2 } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';

import ConfirmModal from '../components/ConfirmModal.jsx';
import Panel from '../components/Panel.jsx';
import { SkeletonRows } from '../components/Skeleton.jsx';
import { authApi } from '../utils/api.js';

const employeeRoles = ['employee', 'manager', 'admin'];
const pageSize = 5;

const emptyStudentFilters = {
  id: '',
  email: '',
  full_name: '',
  group_name: '',
  study_program: '',
  is_active: ''
};

const emptyEmployeeFilters = {
  id: '',
  email: '',
  full_name: '',
  type: '',
  department_name: '',
  position: ''
};

const emptyStudentForm = {
  email: '',
  first_name: '',
  last_name: '',
  middle_name: '',
  is_active: true,
  group_name: '',
  study_program: ''
};

const emptyEmployeeForm = {
  email: '',
  type: 'employee',
  first_name: '',
  last_name: '',
  middle_name: '',
  is_active: true,
  department_name: '',
  position: ''
};

const fallbackStudents = [
  {
    id: 1,
    email: 'student@edu.hse.ru',
    first_name: 'Анна',
    last_name: 'Иванова',
    middle_name: 'Сергеевна',
    type: 'student',
    is_active: true,
    student_profile: { group_name: '22ПИ-3', study_program: 'Прикладная информатика' }
  }
];

const fallbackEmployees = [
  {
    id: 2,
    email: 'employee@hse.ru',
    first_name: 'Илья',
    last_name: 'Петров',
    middle_name: 'Андреевич',
    type: 'employee',
    is_active: true,
    employee_profile: { department_name: 'Факультет информатики', position: 'Преподаватель' }
  },
  {
    id: 3,
    email: 'manager@hse.ru',
    first_name: 'Мария',
    last_name: 'Соколова',
    type: 'manager',
    is_active: true,
    employee_profile: { department_name: 'Учебный офис', position: 'Менеджер' }
  }
];

function fullName(row) {
  return [row.last_name, row.first_name, row.middle_name].filter(Boolean).join(' ') || 'Не указано';
}

function compactParams(params) {
  return Object.fromEntries(
    Object.entries(params).filter(([, value]) => (
      value !== undefined && value !== null && value !== ''
    ))
  );
}

function studentQuery(filters, page) {
  return compactParams({
    type: 'student',
    id: filters.id,
    email: filters.email,
    full_name: filters.full_name,
    group_name: filters.group_name,
    study_program: filters.study_program,
    is_active: filters.is_active,
    limit: pageSize,
    offset: (page - 1) * pageSize
  });
}

function employeeQuery(filters, page) {
  return compactParams({
    types: filters.type ? [filters.type] : employeeRoles,
    id: filters.id,
    email: filters.email,
    full_name: filters.full_name,
    department_name: filters.department_name,
    position: filters.position,
    limit: pageSize,
    offset: (page - 1) * pageSize
  });
}

function normalizeUser(response) {
  return response?.user || null;
}

function applyStudentForm(user, form) {
  return {
    ...user,
    email: form.email,
    type: 'student',
    first_name: form.first_name,
    last_name: form.last_name,
    middle_name: form.middle_name,
    is_active: form.is_active,
    student_profile: {
      ...(user.student_profile || {}),
      group_name: form.group_name,
      study_program: form.study_program
    }
  };
}

function applyEmployeeForm(user, form) {
  return {
    ...user,
    email: form.email,
    type: form.type,
    first_name: form.first_name,
    last_name: form.last_name,
    middle_name: form.middle_name,
    is_active: form.is_active,
    employee_profile: {
      ...(user.employee_profile || {}),
      department_name: form.department_name,
      position: form.position
    }
  };
}

function studentToForm(user = {}) {
  return {
    email: user.email || '',
    first_name: user.first_name || '',
    last_name: user.last_name || '',
    middle_name: user.middle_name || '',
    is_active: user.is_active !== false,
    group_name: user.student_profile?.group_name || '',
    study_program: user.student_profile?.study_program || ''
  };
}

function employeeToForm(user = {}) {
  return {
    email: user.email || '',
    type: employeeRoles.includes(user.type) ? user.type : 'employee',
    first_name: user.first_name || '',
    last_name: user.last_name || '',
    middle_name: user.middle_name || '',
    is_active: user.is_active !== false,
    department_name: user.employee_profile?.department_name || '',
    position: user.employee_profile?.position || ''
  };
}

function studentPayload(form) {
  return {
    email: form.email,
    type: 'student',
    first_name: form.first_name,
    last_name: form.last_name,
    middle_name: form.middle_name,
    is_active: form.is_active,
    student_profile: {
      group_name: form.group_name,
      study_program: form.study_program
    }
  };
}

function employeePayload(form) {
  return {
    email: form.email,
    type: form.type,
    first_name: form.first_name,
    last_name: form.last_name,
    middle_name: form.middle_name,
    is_active: form.is_active,
    employee_profile: {
      department_name: form.department_name,
      position: form.position
    }
  };
}

export default function UserSettingsPage() {
  const [students, setStudents] = useState(fallbackStudents);
  const [employees, setEmployees] = useState(fallbackEmployees);
  const [studentTotal, setStudentTotal] = useState(fallbackStudents.length);
  const [employeeTotal, setEmployeeTotal] = useState(fallbackEmployees.length);
  const [studentPage, setStudentPage] = useState(1);
  const [employeePage, setEmployeePage] = useState(1);
  const [studentFilters, setStudentFilters] = useState(emptyStudentFilters);
  const [employeeFilters, setEmployeeFilters] = useState(emptyEmployeeFilters);
  const [modal, setModal] = useState(null);
  const [confirmDelete, setConfirmDelete] = useState(null);
  const [isStudentsLoading, setIsStudentsLoading] = useState(true);
  const [isEmployeesLoading, setIsEmployeesLoading] = useState(true);

  useEffect(() => {
    loadStudents();
  }, [studentPage, studentFilters]);

  useEffect(() => {
    loadEmployees();
  }, [employeePage, employeeFilters]);

  async function loadStudents() {
    setIsStudentsLoading(true);
    const response = await authApi.users.list(studentQuery(studentFilters, studentPage)).catch(() => null);
    if (response?.users) {
      setStudents(response.users);
      setStudentTotal(response.total_count ?? response.users.length);
    }
    setIsStudentsLoading(false);
  }

  async function loadEmployees() {
    setIsEmployeesLoading(true);
    const response = await authApi.users.list(employeeQuery(employeeFilters, employeePage)).catch(() => null);
    if (response?.users) {
      setEmployees(response.users);
      setEmployeeTotal(response.total_count ?? response.users.length);
    }
    setIsEmployeesLoading(false);
  }

  function updateStudentFilter(field, value) {
    setStudentPage(1);
    setStudentFilters((current) => ({ ...current, [field]: value }));
  }

  function updateEmployeeFilter(field, value) {
    setEmployeePage(1);
    setEmployeeFilters((current) => ({ ...current, [field]: value }));
  }

  async function saveStudent(form) {
    const payload = studentPayload(form);
    const saved = modal?.user
      ? normalizeUser(await authApi.users.update(modal.user.id, payload))
      : normalizeUser(await authApi.users.create(payload));

    if (saved) {
      const updatedStudent = applyStudentForm(saved, form);
      setStudents((current) => (
        modal?.user
          ? current.map((user) => (user.id === updatedStudent.id ? updatedStudent : user))
          : [updatedStudent, ...current]
      ));
      if (!modal?.user) setStudentTotal((current) => current + 1);
    }
    setModal(null);
  }

  async function saveEmployee(form) {
    const payload = employeePayload(form);
    const saved = modal?.user
      ? normalizeUser(await authApi.users.update(modal.user.id, payload))
      : normalizeUser(await authApi.users.create(payload));

    if (saved) {
      const updatedEmployee = applyEmployeeForm(saved, form);
      setEmployees((current) => (
        modal?.user
          ? current.map((user) => (user.id === updatedEmployee.id ? updatedEmployee : user))
          : [updatedEmployee, ...current]
      ));
      if (!modal?.user) setEmployeeTotal((current) => current + 1);
    }
    setModal(null);
  }

  async function removeStudent(row) {
    await authApi.users.remove(row.id).catch(() => {});
    setStudents((current) => current.filter((user) => user.id !== row.id));
    setStudentTotal((current) => Math.max(current - 1, 0));
    setConfirmDelete(null);
  }

  async function removeEmployee(row) {
    await authApi.users.remove(row.id).catch(() => {});
    setEmployees((current) => current.filter((user) => user.id !== row.id));
    setEmployeeTotal((current) => Math.max(current - 1, 0));
    setConfirmDelete(null);
  }

  function requestRemove(kind, row) {
    setConfirmDelete({
      title: 'Удаление пользователя',
      message: 'Вы уверены, что хотите удалить этого пользователя?',
      onConfirm: () => (kind === 'student' ? removeStudent(row) : removeEmployee(row))
    });
  }

  return (
    <>
      <div className="user-settings-grid">
        <UserWidget
          title="Студенты"
          addLabel="Добавить студента"
          rows={students}
          filters={studentFilters}
          page={studentPage}
          total={studentTotal}
          onFilterChange={updateStudentFilter}
          onPageChange={setStudentPage}
          isLoading={isStudentsLoading}
          columns={[
            { key: 'id', label: 'ID', width: '12ch', filterKey: 'id', filterType: 'number' },
            { key: 'email', label: 'Почта', filterKey: 'email' },
            { key: 'name', label: 'ФИО', filterKey: 'full_name', render: fullName },
            { key: 'group', label: 'Группа', filterKey: 'group_name', render: (row) => row.student_profile?.group_name || '-' },
            { key: 'program', label: 'Программа', filterKey: 'study_program', render: (row) => row.student_profile?.study_program || '-' },
            {
              key: 'status',
              label: 'Статус',
              filterKey: 'is_active',
              filterType: 'status',
              render: (row) => (row.is_active ? 'Активен' : 'Отключен')
            },
            {
              key: 'actions',
              label: 'Действия',
              width: '116px',
              render: (row) => (
                <RowActions
                  onEdit={() => setModal({ kind: 'student', user: row })}
                  onRemove={() => requestRemove('student', row)}
                />
              )
            }
          ]}
          onAdd={() => setModal({ kind: 'student' })}
        />

        <UserWidget
          title="Сотрудники"
          addLabel="Добавить сотрудника"
          rows={employees}
          filters={employeeFilters}
          page={employeePage}
          total={employeeTotal}
          onFilterChange={updateEmployeeFilter}
          onPageChange={setEmployeePage}
          isLoading={isEmployeesLoading}
          columns={[
            { key: 'id', label: 'ID', width: '12ch', filterKey: 'id', filterType: 'number' },
            { key: 'email', label: 'Почта', filterKey: 'email' },
            { key: 'name', label: 'ФИО', filterKey: 'full_name', render: fullName },
            { key: 'type', label: 'Роль', filterKey: 'type', filterType: 'role' },
            { key: 'department', label: 'Подразделение', filterKey: 'department_name', render: (row) => row.employee_profile?.department_name || '-' },
            { key: 'position', label: 'Должность', filterKey: 'position', render: (row) => row.employee_profile?.position || '-' },
            {
              key: 'actions',
              label: 'Действия',
              width: '116px',
              render: (row) => (
                <RowActions
                  onEdit={() => setModal({ kind: 'employee', user: row })}
                  onRemove={() => requestRemove('employee', row)}
                />
              )
            }
          ]}
          onAdd={() => setModal({ kind: 'employee' })}
        />
      </div>

      {modal?.kind === 'student' && (
        <UserModal
          title={modal.user ? 'Редактирование студента' : 'Новый студент'}
          initialValues={modal.user ? studentToForm(modal.user) : emptyStudentForm}
          type="student"
          onClose={() => setModal(null)}
          onSubmit={saveStudent}
        />
      )}

      {modal?.kind === 'employee' && (
        <UserModal
          title={modal.user ? 'Редактирование сотрудника' : 'Новый сотрудник'}
          initialValues={modal.user ? employeeToForm(modal.user) : emptyEmployeeForm}
          type="employee"
          onClose={() => setModal(null)}
          onSubmit={saveEmployee}
        />
      )}
      {confirmDelete && (
        <ConfirmModal
          title={confirmDelete.title}
          message={confirmDelete.message}
          confirmLabel="Да"
          cancelLabel="Нет"
          onCancel={() => setConfirmDelete(null)}
          onConfirm={confirmDelete.onConfirm}
        />
      )}
    </>
  );
}

function UserWidget({
  title,
  addLabel,
  rows,
  columns,
  filters,
  page,
  total,
  onFilterChange,
  onPageChange,
  onAdd,
  isLoading
}) {
  return (
    <Panel
      className="user-widget"
      title={title}
      action={(
        <button className="button button--primary user-widget__action" type="button" onClick={onAdd}>
          <Plus size={17} />
          {addLabel}
        </button>
      )}
    >
      <UserTable
        columns={columns}
        rows={rows}
        filters={filters}
        onFilterChange={onFilterChange}
        isLoading={isLoading}
      />
      <Pagination page={page} total={total} onPageChange={onPageChange} />
    </Panel>
  );
}

function UserTable({ columns, rows, filters, onFilterChange, isLoading }) {
  const template = columns.map((col) => col.width || '1fr').join(' ');

  return (
    <div className="user-table">
      <div className="user-table__head" style={{ gridTemplateColumns: template }}>
        {columns.map((col) => (
          <div className="user-table__head-cell" key={col.key}>
            <span>{col.label}</span>
            {col.filterKey && (
              <FilterControl
                column={col}
                value={filters[col.filterKey] || ''}
                onChange={(value) => onFilterChange(col.filterKey, value)}
              />
            )}
          </div>
        ))}
      </div>
      {isLoading ? (
        <SkeletonRows rows={5} />
      ) : rows.length ? rows.map((row, index) => (
        <div
          className="user-table__row"
          style={{ gridTemplateColumns: template }}
          key={row.id || index}
        >
          {columns.map((col) => (
            <div key={col.key}>
              {col.render ? col.render(row, index) : row[col.key]}
            </div>
          ))}
        </div>
      )) : (
        <div className="user-table__empty">Ничего не найдено</div>
      )}
    </div>
  );
}

function FilterControl({ column, value, onChange }) {
  if (column.filterType === 'status') {
    return (
      <select value={value} onChange={(event) => onChange(event.target.value)}>
        <option value="">Все</option>
        <option value="true">Активен</option>
        <option value="false">Отключен</option>
      </select>
    );
  }

  if (column.filterType === 'role') {
    return (
      <select value={value} onChange={(event) => onChange(event.target.value)}>
        <option value="">Все</option>
        {employeeRoles.map((role) => <option key={role} value={role}>{role}</option>)}
      </select>
    );
  }

  return (
    <input
      type={column.filterType === 'number' ? 'number' : 'text'}
      value={value}
      onChange={(event) => onChange(event.target.value)}
    />
  );
}

function Pagination({ page, total, onPageChange }) {
  const totalPages = Math.max(Math.ceil(total / pageSize), 1);
  const from = total === 0 ? 0 : ((page - 1) * pageSize) + 1;
  const to = Math.min(page * pageSize, total);

  return (
    <div className="user-pagination">
      <span>{from}-{to} из {total}</span>
      <div className="user-pagination__buttons">
        <button
          className="icon-ghost"
          type="button"
          aria-label="Предыдущая страница"
          disabled={page <= 1}
          onClick={() => onPageChange(page - 1)}
        >
          <ChevronLeft size={20} />
        </button>
        <span>{page} / {totalPages}</span>
        <button
          className="icon-ghost"
          type="button"
          aria-label="Следующая страница"
          disabled={page >= totalPages}
          onClick={() => onPageChange(page + 1)}
        >
          <ChevronRight size={20} />
        </button>
      </div>
    </div>
  );
}

function RowActions({ onEdit, onRemove }) {
  return (
    <div className="table-actions">
      <button className="action-button action-button--edit" type="button" aria-label="Редактировать" onClick={onEdit}>
        <Edit3 size={15} />
      </button>
      <button className="action-button action-button--delete" type="button" aria-label="Удалить" onClick={onRemove}>
        <Trash2 size={15} />
      </button>
    </div>
  );
}

function UserModal({ title, initialValues, type, onClose, onSubmit }) {
  const [form, setForm] = useState(initialValues);
  const isEmployee = type === 'employee';

  const canSubmit = useMemo(() => form.email.trim().length > 0, [form.email]);

  function updateField(field, value) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  async function submit(event) {
    event.preventDefault();
    if (!canSubmit) return;
    await onSubmit(form);
  }

  return (
    <div className="modal-backdrop">
      <form className="user-modal" onSubmit={submit}>
        <h2>{title}</h2>

        <div className="user-form-grid">
          <label>
            <span>Почта</span>
            <input value={form.email} onChange={(event) => updateField('email', event.target.value)} />
          </label>
          <label>
            <span>Фамилия</span>
            <input value={form.last_name} onChange={(event) => updateField('last_name', event.target.value)} />
          </label>
          <label>
            <span>Имя</span>
            <input value={form.first_name} onChange={(event) => updateField('first_name', event.target.value)} />
          </label>
          <label>
            <span>Отчество</span>
            <input value={form.middle_name} onChange={(event) => updateField('middle_name', event.target.value)} />
          </label>

          {isEmployee ? (
            <>
              <label>
                <span>Роль</span>
                <select value={form.type} onChange={(event) => updateField('type', event.target.value)}>
                  {employeeRoles.map((role) => <option key={role} value={role}>{role}</option>)}
                </select>
              </label>
              <label>
                <span>Подразделение</span>
                <input value={form.department_name} onChange={(event) => updateField('department_name', event.target.value)} />
              </label>
              <label>
                <span>Должность</span>
                <input value={form.position} onChange={(event) => updateField('position', event.target.value)} />
              </label>
            </>
          ) : (
            <>
              <label>
                <span>Группа</span>
                <input value={form.group_name} onChange={(event) => updateField('group_name', event.target.value)} />
              </label>
              <label>
                <span>Программа</span>
                <input value={form.study_program} onChange={(event) => updateField('study_program', event.target.value)} />
              </label>
            </>
          )}

          <label className="user-toggle">
            <input
              type="checkbox"
              checked={form.is_active}
              onChange={(event) => updateField('is_active', event.target.checked)}
            />
            <span>Активный пользователь</span>
          </label>
        </div>

        <div className="modal-actions">
          <button className="button button--danger" type="button" onClick={onClose}>
            Отменить
          </button>
          <button className="button button--primary" type="submit" disabled={!canSubmit}>
            Сохранить
          </button>
        </div>
      </form>
    </div>
  );
}
