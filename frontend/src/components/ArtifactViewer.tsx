import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {
  X,
  Copy,
  Check,
  Download,
  Eye,
  Code2,
  ShieldCheck
} from 'lucide-react';
import type { ArtifactPayload } from '../types';

interface ArtifactViewerProps {
  artifact: ArtifactPayload;
  onClose: () => void;
}

export const ArtifactViewer: React.FC<ArtifactViewerProps> = ({
  artifact,
  onClose,
}) => {
  const [activeTab, setActiveTab] = useState<'preview' | 'source'>('preview');
  const [copied, setCopied] = useState(false);

  const isHtml = artifact.type.toLowerCase() === 'html';
  const displayContent = artifact.sanitized_content || artifact.content;

  const handleCopy = () => {
    navigator.clipboard.writeText(artifact.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const ext = isHtml ? 'html' : 'md';
    const blob = new Blob([artifact.content], {
      type: isHtml ? 'text/html;charset=utf-8' : 'text/markdown;charset=utf-8'
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${artifact.title.toLowerCase().replace(/[^a-z0-9]+/g, '-')}.${ext}`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  // Safe wrapper template for untrusted HTML in isolated iframe
  const iframeDocument = isHtml
    ? `<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    body {
      margin: 0;
      padding: 24px;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      color: #0f172a;
      background-color: #f8fafc;
      line-height: 1.6;
    }
  </style>
</head>
<body>
  ${displayContent}
</body>
</html>`
    : '';

  return (
    <aside className="w-full md:w-[480px] lg:w-[560px] h-full bg-slate-900 border-l border-slate-800 flex flex-col select-none shrink-0 z-20 shadow-2xl transition-all">
      {/* Top Header */}
      <div className="h-14 px-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/90">
        <div className="flex items-center space-x-2 truncate mr-2">
          <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 shrink-0 font-semibold">
            {artifact.type}
          </span>
          <h3 className="text-xs font-semibold text-white truncate" title={artifact.title}>
            {artifact.title}
          </h3>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center space-x-1 shrink-0">
          <button
            onClick={handleCopy}
            className="p-1.5 text-slate-400 hover:text-white rounded-md hover:bg-slate-800 transition-colors"
            title="Copy to clipboard"
          >
            {copied ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
          </button>
          <button
            onClick={handleDownload}
            className="p-1.5 text-slate-400 hover:text-white rounded-md hover:bg-slate-800 transition-colors"
            title="Download file"
          >
            <Download className="w-4 h-4" />
          </button>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-white rounded-md hover:bg-slate-800 transition-colors ml-1"
            title="Close Artifact panel"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Subheader: Tabs & Security Badge */}
      <div className="px-4 py-2 border-b border-slate-800/80 bg-slate-950/40 flex items-center justify-between">
        <div className="flex items-center space-x-1 bg-slate-800/70 p-0.5 rounded-lg text-xs">
          <button
            onClick={() => setActiveTab('preview')}
            className={`flex items-center space-x-1.5 px-3 py-1 rounded-md transition-all font-medium ${
              activeTab === 'preview'
                ? 'bg-blue-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Eye className="w-3.5 h-3.5" />
            <span>Preview</span>
          </button>
          <button
            onClick={() => setActiveTab('source')}
            className={`flex items-center space-x-1.5 px-3 py-1 rounded-md transition-all font-medium ${
              activeTab === 'source'
                ? 'bg-blue-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Code2 className="w-3.5 h-3.5" />
            <span>Source</span>
          </button>
        </div>

        {/* Security Indicator */}
        <div className="flex items-center space-x-1 text-[11px] text-emerald-400">
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>Sanitized & Isolated</span>
        </div>
      </div>

      {/* Main Artifact Body */}
      <div className="flex-1 overflow-hidden relative bg-slate-950">
        {activeTab === 'preview' ? (
          isHtml ? (
            /* Sandboxed isolated Iframe preventing script execution and token theft */
            <iframe
              title={artifact.title}
              srcDoc={iframeDocument}
              sandbox="allow-same-origin"
              className="w-full h-full border-none bg-slate-50"
            />
          ) : (
            /* Rendered Markdown */
            <div className="w-full h-full overflow-y-auto p-6 prose-custom text-sm">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {displayContent}
              </ReactMarkdown>
            </div>
          )
        ) : (
          /* Raw Source Code Tab */
          <div className="w-full h-full overflow-y-auto p-4 font-mono text-xs text-slate-300 bg-slate-950 select-text">
            <pre className="whitespace-pre-wrap leading-relaxed">
              {artifact.content}
            </pre>
          </div>
        )}
      </div>
    </aside>
  );
};
