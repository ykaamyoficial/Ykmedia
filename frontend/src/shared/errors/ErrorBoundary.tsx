import { Component, type ErrorInfo, type ReactNode } from "react";

import { YkButton } from "@/components/system/YkButton";
import { YkEmptyState } from "@/components/system/YkEmptyState";
import { YkIcons } from "@/shared/icons";

type ErrorBoundaryProps = {
  children: ReactNode;
};

type ErrorBoundaryState = {
  hasError: boolean;
};

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = { hasError: false };

  static getDerivedStateFromError(): ErrorBoundaryState {
    return { hasError: true };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("Frontend boundary captured an error.", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <main className="min-h-0 flex-1 overflow-auto bg-background p-5">
          <YkEmptyState
            icon={YkIcons.AlertCircle}
            title="Algo saiu do esperado"
            description="A area atual falhou, mas a navegacao permanece disponivel."
            action={
              <YkButton type="button" onClick={() => this.setState({ hasError: false })}>
                Tentar novamente
              </YkButton>
            }
          />
        </main>
      );
    }

    return this.props.children;
  }
}
