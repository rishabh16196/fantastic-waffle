import { useEffect, useState, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getRole, RoleDetail, DefinitionWithExamples } from '../api';
import './ResultsView.css';

interface ModalData {
  definition: DefinitionWithExamples;
  levelName: string;
  competencyName: string;
  levelIdx: number;
  compIdx: number;
}

export default function ResultsView() {
  const { roleId } = useParams<{ roleId: string }>();
  const [role, setRole] = useState<RoleDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [modalData, setModalData] = useState<ModalData | null>(null);
  const [compareMode, setCompareMode] = useState(false);

  useEffect(() => {
    if (!roleId) return;

    const fetchRole = async () => {
      try {
        const data = await getRole(roleId);
        setRole(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load results');
      } finally {
        setLoading(false);
      }
    };

    fetchRole();
  }, [roleId]);

  // Close modal on Escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setModalData(null);
        setCompareMode(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const openModal = useCallback((
    definition: DefinitionWithExamples,
    levelName: string,
    competencyName: string,
    levelIdx: number,
    compIdx: number
  ) => {
    setModalData({ definition, levelName, competencyName, levelIdx, compIdx });
    setCompareMode(false);
  }, []);

  const closeModal = useCallback(() => {
    setModalData(null);
    setCompareMode(false);
  }, []);

  const navigateModal = useCallback((direction: 'prev' | 'next') => {
    if (!modalData || !role) return;

    const { levelIdx, compIdx } = modalData;
    let newLevelIdx = levelIdx;
    let newCompIdx = compIdx;

    if (direction === 'next') {
      newLevelIdx++;
      if (newLevelIdx >= role.levels.length) {
        newLevelIdx = 0;
        newCompIdx++;
        if (newCompIdx >= role.competencies.length) {
          newCompIdx = 0;
        }
      }
    } else {
      newLevelIdx--;
      if (newLevelIdx < 0) {
        newLevelIdx = role.levels.length - 1;
        newCompIdx--;
        if (newCompIdx < 0) {
          newCompIdx = role.competencies.length - 1;
        }
      }
    }

    const newLevel = role.levels[newLevelIdx];
    const newComp = role.competencies[newCompIdx];
    const newDef = role.definitions.find(d => 
      d.level_id === newLevel.id && d.competency_id === newComp.id
    );

    if (newDef) {
      setModalData({
        definition: newDef,
        levelName: newLevel.name,
        competencyName: newComp.name,
        levelIdx: newLevelIdx,
        compIdx: newCompIdx
      });
      setCompareMode(false);
    }
  }, [modalData, role]);

  // Get next level definition for comparison
  const getNextLevelData = useCallback(() => {
    if (!modalData || !role) return null;

    const nextLevelIdx = modalData.levelIdx + 1;
    if (nextLevelIdx >= role.levels.length) return null;

    const nextLevel = role.levels[nextLevelIdx];
    const currentComp = role.competencies[modalData.compIdx];
    
    const nextDef = role.definitions.find(d => 
      d.level_id === nextLevel.id && d.competency_id === currentComp.id
    );

    if (!nextDef) return null;

    return {
      definition: nextDef,
      levelName: nextLevel.name
    };
  }, [modalData, role]);

  if (loading) {
    return (
      <div className="results-page">
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>Loading your results...</p>
        </div>
      </div>
    );
  }

  if (error || !role) {
    return (
      <div className="results-page">
        <div className="error-container">
          <h2>Something went wrong</h2>
          <p>{error || 'Role not found'}</p>
          <Link to="/dashboard" className="btn btn-primary">Back to Dashboard</Link>
        </div>
      </div>
    );
  }

  // Create a map for quick definition lookup by level_id + competency_id
  const definitionMap = new Map<string, DefinitionWithExamples>();
  role.definitions.forEach((def) => {
    const key = `${def.level_id}-${def.competency_id}`;
    definitionMap.set(key, def);
  });

  const nextLevelData = getNextLevelData();
  const canCompare = nextLevelData !== null;
  const isAtMaxLevel = modalData && modalData.levelIdx >= role.levels.length - 1;

  return (
    <div className="results-page">
      <div className="results-container">
        <header className="results-header animate-fade-in">
          <Link to="/dashboard" className="back-link">← Back to Dashboard</Link>
          <h1>{role.name} Leveling Guide</h1>
          <p className="role-meta">
            {role.levels.length} levels • {role.competencies.length} competencies
          </p>
        </header>

        <div className="results-grid animate-fade-in stagger-1">
          {/* Header row - Levels as columns (career progression left→right) */}
          <div className="grid-header">
            <div className="grid-corner">Competency</div>
            {role.levels.map((level) => (
              <div key={level.id} className="grid-level-header">
                {level.name}
              </div>
            ))}
          </div>

          {/* Data rows - Competencies as rows */}
          {role.competencies.map((comp, compIdx) => (
            <div key={comp.id} className="grid-row" style={{ animationDelay: `${0.1 * (compIdx + 2)}s` }}>
              <div className="grid-competency-label">{comp.name}</div>
              {role.levels.map((level, levelIdx) => {
                const definition = definitionMap.get(`${level.id}-${comp.id}`);
                
                return (
                  <div
                    key={`${level.id}-${comp.id}`}
                    className="grid-cell"
                    onClick={() => definition && openModal(definition, level.name, comp.name, levelIdx, compIdx)}
                  >
                    {definition ? (
                      <>
                        <div className="cell-requirement">
                          {definition.definition}
                        </div>
                        {definition.examples.length > 0 && (
                          <div className="cell-expand-hint">
                            {definition.examples.length} examples
                          </div>
                        )}
                      </>
                    ) : (
                      <span className="no-data">No data</span>
                    )}
                  </div>
                );
              })}
            </div>
          ))}
        </div>

        <footer className="results-footer animate-fade-in stagger-3">
          <p>
            Generated on {new Date(role.created_at).toLocaleDateString()} • 
            Click any cell to see specific examples
          </p>
        </footer>
      </div>

      {/* Modal */}
      {modalData && (
        <div className="modal-overlay" onClick={closeModal}>
          <div 
            className={`modal-content ${compareMode ? 'compare-mode' : ''}`} 
            onClick={(e) => e.stopPropagation()}
          >
            <button className="modal-close" onClick={closeModal}>×</button>
            
            {!compareMode ? (
              // Single view mode
              <>
                <div className="modal-header">
                  <span className="modal-level">{modalData.levelName}</span>
                  <span className="modal-separator">×</span>
                  <span className="modal-competency">{modalData.competencyName}</span>
                </div>

                <div className="modal-body">
                  <div className="modal-section">
                    <h3>Requirement</h3>
                    <p className="modal-requirement">{modalData.definition.definition}</p>
                  </div>

                  {modalData.definition.examples.length > 0 && (
                    <div className="modal-section">
                      <h3>What this looks like in practice</h3>
                      <ul className="modal-examples">
                        {modalData.definition.examples.map((example, idx) => (
                          <li key={example.id}>
                            <span className="example-number">{idx + 1}.</span>
                            {example.content}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>

                <div className="modal-footer">
                  <button className="btn btn-secondary" onClick={() => navigateModal('prev')}>
                    ← Previous
                  </button>
                  {canCompare ? (
                    <button className="btn btn-primary" onClick={() => setCompareMode(true)}>
                      Compare with {nextLevelData.levelName} →
                    </button>
                  ) : (
                    <button className="btn btn-secondary" disabled title="Already at highest level">
                      {isAtMaxLevel ? 'Highest Level' : 'No next level'}
                    </button>
                  )}
                  <button className="btn btn-secondary" onClick={() => navigateModal('next')}>
                    Next →
                  </button>
                </div>
              </>
            ) : (
              // Compare mode - side by side
              <>
                <div className="modal-header compare-header">
                  <span className="modal-competency">{modalData.competencyName}</span>
                  <span className="compare-badge">Comparison View</span>
                </div>

                <div className="compare-container">
                  {/* Current Level */}
                  <div className="compare-column current">
                    <div className="compare-level-badge">{modalData.levelName}</div>
                    
                    <div className="modal-section">
                      <h3>Requirement</h3>
                      <p className="modal-requirement">{modalData.definition.definition}</p>
                    </div>

                    {modalData.definition.examples.length > 0 && (
                      <div className="modal-section">
                        <h3>Examples</h3>
                        <ul className="modal-examples">
                          {modalData.definition.examples.map((example, idx) => (
                            <li key={example.id}>
                              <span className="example-number">{idx + 1}.</span>
                              {example.content}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>

                  {/* Arrow */}
                  <div className="compare-arrow">→</div>

                  {/* Next Level */}
                  {nextLevelData && (
                    <div className="compare-column next">
                      <div className="compare-level-badge next-level">{nextLevelData.levelName}</div>
                      
                      <div className="modal-section">
                        <h3>Requirement</h3>
                        <p className="modal-requirement">{nextLevelData.definition.definition}</p>
                      </div>

                      {nextLevelData.definition.examples.length > 0 && (
                        <div className="modal-section">
                          <h3>Examples</h3>
                          <ul className="modal-examples">
                            {nextLevelData.definition.examples.map((example, idx) => (
                              <li key={example.id}>
                                <span className="example-number">{idx + 1}.</span>
                                {example.content}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  )}
                </div>

                <div className="modal-footer">
                  <button className="btn btn-secondary" onClick={() => setCompareMode(false)}>
                    ← Back to Single View
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
