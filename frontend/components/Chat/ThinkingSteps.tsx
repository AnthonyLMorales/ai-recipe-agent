"use client";

interface ThinkingStep {
  node: string;
  message: string;
  completed: boolean;
}

interface ThinkingStepsProps {
  steps: ThinkingStep[];
}

export function ThinkingSteps({ steps }: ThinkingStepsProps) {
  if (steps.length === 0) return null;

  return (
    <div className="flex flex-col gap-2 p-4 bg-gray-50 rounded-lg border border-gray-200">
      {steps.map((step) => (
        <div key={step.node} className="flex items-center gap-3">
          {/* Icon */}
          <div className="flex-shrink-0">
            {step.completed ? (
              <svg
                className="w-5 h-5 text-green-500"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M5 13l4 4L19 7"
                />
              </svg>
            ) : (
              <div className="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
            )}
          </div>

          {/* Message */}
          <span
            className={`text-sm ${step.completed ? "text-gray-600" : "text-gray-900 font-medium"}`}
          >
            {step.message}
          </span>
        </div>
      ))}
    </div>
  );
}
