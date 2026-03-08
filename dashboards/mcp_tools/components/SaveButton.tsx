"use client";

interface SaveButtonProps {
  onSave: () => void;
  disabled?: boolean;
}

export function SaveButton({ onSave, disabled }: SaveButtonProps) {
  return (
    <button
      type="button"
      onClick={onSave}
      disabled={disabled}
      className="rounded-lg bg-[var(--primary)] px-4 py-2.5 text-sm font-medium text-white transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
    >
      Save
    </button>
  );
}
