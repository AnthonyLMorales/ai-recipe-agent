interface ErrorMessageProps {
  message: string;
  onDismiss?: () => void;
}

export function ErrorMessage({ message, onDismiss }: ErrorMessageProps) {
  return (
    <div className="bg-red-50 border border-red-200 text-red-800 dark:bg-red-900/20 dark:border-red-800 dark:text-red-200 p-3 rounded-lg flex items-center justify-between">
      <span>{message}</span>
      {onDismiss && (
        <button
          onClick={onDismiss}
          className="ml-4 text-red-600 dark:text-red-400 hover:text-red-800 dark:hover:text-red-200 font-bold"
          aria-label="Dismiss error"
        >
          ×
        </button>
      )}
    </div>
  );
}
