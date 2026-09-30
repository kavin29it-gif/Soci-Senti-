import { Component, type ErrorInfo, type ReactNode } from 'react';
import { AlertOctagon, RefreshCw } from 'lucide-react';

interface Props {
  children: ReactNode;
  fallbackTitle?: string;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught error in component:', error, errorInfo);
  }

  public handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  public render() {
    if (this.state.hasError) {
      return (
        <div className="glass-panel p-8 my-8 max-w-2xl mx-auto rounded-[22px] border border-[#ff7a1a]/40 shadow-2xl text-center space-y-4 animate-fade-in font-['Manrope']">
          <div className="w-12 h-12 mx-auto rounded-full bg-[rgba(255,122,26,0.15)] border border-[#ff7a1a]/40 flex items-center justify-center text-[#ff7a1a]">
            <AlertOctagon className="w-6 h-6" />
          </div>
          <h2 className="text-lg font-extrabold text-[#fff3e8] font-['Sora']">
            {this.props.fallbackTitle || 'Component Render Error'}
          </h2>
          <p className="text-xs text-[rgba(255,226,205,0.64)] max-w-md mx-auto">
            An unexpected error occurred while rendering this module. You can attempt to reload or navigate to another view.
          </p>
          {this.state.error && (
            <div className="p-3.5 rounded-xl bg-black/60 border border-[rgba(255,196,140,0.15)] text-left font-mono text-[11px] text-[#ffd9b8] max-h-32 overflow-y-auto">
              {this.state.error.message}
            </div>
          )}
          <div className="pt-2 flex justify-center space-x-3">
            <button
              onClick={this.handleReset}
              className="px-4 py-2 text-xs font-bold rounded-xl bg-gradient-to-r from-[#ff7a1a] via-[#ff9a4d] to-[#ffd9b8] text-[#0b0603] hover:brightness-110 flex items-center space-x-1.5 transition-all shadow-md shadow-[#ff7a1a]/30 cursor-pointer active:scale-95"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Retry Component</span>
            </button>
            <button
              onClick={() => window.location.reload()}
              className="px-4 py-2 text-xs font-semibold rounded-xl bg-[rgba(255,154,77,0.08)] hover:bg-[rgba(255,154,77,0.16)] text-[#fff3e8] border border-[rgba(255,196,140,0.2)] transition-all cursor-pointer"
            >
              Reload Page
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
