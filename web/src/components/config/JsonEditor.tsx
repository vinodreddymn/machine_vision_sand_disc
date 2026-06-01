/**
 * JSON Editor Component
 * Allows editing JSON configurations with syntax highlighting and validation
 */

import { useState, useCallback } from 'react';
import '../../styles/json-editor.css';

interface JsonEditorProps {
  value: Record<string, any>;
  onChange: (value: Record<string, any>) => void;
  readOnly?: boolean;
  onSave?: () => void;
  isSaving?: boolean;
  error?: string;
}

export function JsonEditor({
  value,
  onChange,
  readOnly = false,
  onSave,
  isSaving = false,
  error,
}: JsonEditorProps) {
  const [jsonText, setJsonText] = useState(JSON.stringify(value, null, 2));
  const [parseError, setParseError] = useState<string | null>(null);

  const handleTextChange = useCallback((e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const text = e.target.value;
    setJsonText(text);

    try {
      const parsed = JSON.parse(text);
      onChange(parsed);
      setParseError(null);
    } catch (err) {
      setParseError((err as Error).message);
    }
  }, [onChange]);

  const handleFormat = useCallback(() => {
    try {
      const parsed = JSON.parse(jsonText);
      setJsonText(JSON.stringify(parsed, null, 2));
      onChange(parsed);
      setParseError(null);
    } catch (err) {
      setParseError((err as Error).message);
    }
  }, [jsonText, onChange]);

  const handleMinify = useCallback(() => {
    try {
      const parsed = JSON.parse(jsonText);
      setJsonText(JSON.stringify(parsed));
      onChange(parsed);
      setParseError(null);
    } catch (err) {
      setParseError((err as Error).message);
    }
  }, [jsonText, onChange]);

  return (
    <div className="json-editor">
      <div className="json-editor-header">
        <div className="json-editor-actions">
          {!readOnly && (
            <>
              <button onClick={handleFormat} className="editor-btn" title="Format JSON">
                Format
              </button>
              <button onClick={handleMinify} className="editor-btn" title="Minify JSON">
                Minify
              </button>
              {onSave && (
                <button
                  onClick={onSave}
                  className="editor-btn save-btn"
                  disabled={isSaving || parseError !== null}
                  title={parseError ? 'Fix JSON errors first' : 'Save configuration'}
                >
                  {isSaving ? 'Saving...' : 'Save'}
                </button>
              )}
            </>
          )}
        </div>
      </div>

      {(error || parseError) && (
        <div className="json-editor-error">
          <strong>Error:</strong> {error || parseError}
        </div>
      )}

      <textarea
        value={jsonText}
        onChange={handleTextChange}
        readOnly={readOnly}
        className={`json-editor-textarea ${parseError ? 'error' : ''}`}
        spellCheck="false"
      />

      <div className="json-editor-footer">
        <span className="json-editor-status">
          {parseError ? (
            <span className="status-error">Invalid JSON</span>
          ) : (
            <span className="status-valid">Valid JSON</span>
          )}
        </span>
        <span className="json-editor-size">
          {jsonText.length} characters
        </span>
      </div>
    </div>
  );
}
