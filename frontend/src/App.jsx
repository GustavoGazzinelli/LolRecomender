import { useState } from "react";

function App() {
  const [jogador, setJogador] = useState("");
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [championIndex, setChampionIndex] = useState(0);

  async function handleSearch() {
    if (!jogador) return;

    setLoading(true);
    setData(null);

    try {
      const response = await fetch(
        `http://127.0.0.1:8000/recomenda/${encodeURIComponent(jogador)}`
      );

      const result = await response.json();
      setData(result);
      setChampionIndex(0);
    } catch (err) {
      console.error("Erro ao buscar recomendações:", err);
    } finally {
      setLoading(false);
    }
  }

  const recomendacoes = data?.recomendacoes ?? [];
  const totalRecomendacoes = recomendacoes.length;
  const campeaoAtual =
    totalRecomendacoes > 0 ? recomendacoes[championIndex] : null;

  function goPrevChampion() {
    if (totalRecomendacoes === 0) return;
    setChampionIndex((i) => (i === 0 ? totalRecomendacoes - 1 : i - 1));
  }

  function goNextChampion() {
    if (totalRecomendacoes === 0) return;
    setChampionIndex((i) =>
      i === totalRecomendacoes - 1 ? 0 : i + 1
    );
  }

  return (
    <main className="app">
      <header className="app__hero">
        <h1 className="app__title">Recomendação de campeões</h1>
        <p className="app__subtitle">
          Descubra campeões alinhados ao seu estilo de
          jogo.
        </p>
      </header>

      <div className="app__search-wrap">
        <div className="app__search">
          <input
            className="app__input"
            value={jogador}
            onChange={(e) => setJogador(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSearch()}
            placeholder="Nome#TAG"
            aria-label="Riot ID (nome e tag)"
          />
          <button
            className="app__btn"
            type="button"
            onClick={handleSearch}
            disabled={loading}
          >
            Buscar
          </button>
        </div>
        {loading && (
          <div
            className="app__loading"
            role="status"
            aria-live="polite"
            aria-busy="true"
          >
            <span className="app__loading-sr">Carregando recomendações…</span>
            <span className="app__loading-dot" aria-hidden="true" />
            <span className="app__loading-dot" aria-hidden="true" />
            <span className="app__loading-dot" aria-hidden="true" />
          </div>
        )}
      </div>

      {data && (
        <section className="app__panel" aria-live="polite">
          <div className="app__panel-layout">
            <div className="app__panel-aside">
              <p className="app__title">Recomendações</p>
              {campeaoAtual ? (
                <>
                  <div
                    className="app__champ-carousel"
                    role="group"
                    aria-label="Campeões recomendados"
                  >
                    <button
                      type="button"
                      className="app__champ-carousel-btn"
                      onClick={goPrevChampion}
                      aria-label="Campeão anterior"
                    >
                      &#10094;
                    </button>
                    <article className="app__champ-card app__champ-card--solo">
                        <h3 className="app__champ-name">{campeaoAtual.nome}</h3>
                        {campeaoAtual.splash && (
                          <img
                            className="app__champ-icon"
                            src={campeaoAtual.splash}
                            alt={`Ícone do campeão ${campeaoAtual.nome}`}
                            loading="lazy"
                          />
                        )}
                        
                      <p className="app__champ-meta">
                        <span>
                          <strong>Tags:</strong> {campeaoAtual.tags}
                        </span>
                      </p>
                    </article>
                    <button
                      type="button"
                      className="app__champ-carousel-btn"
                      onClick={goNextChampion}
                      aria-label="Próximo campeão"
                    >
                      &#10095;
                    </button>
                  </div>
                  <p className="app__champ-carousel-count" aria-live="polite">
                    {championIndex + 1} de {totalRecomendacoes}
                  </p>
                </>
              ) : (
                <p className="app__champ-carousel-empty">
                  Nenhuma recomendação disponível.
                </p>
              )}
            </div>
            <div className="app__panel-main">
              <div className="app__panel-header">
                <h2 className="app__invoker">{data.invocador}</h2>
                <span className="app__badge">{data.perfil_identificado}</span>
              </div>

              <p className="app__section-label">Estatísticas médias</p>
              <div className="app__stats">
                <div className="app__stat">
                  <p className="app__stat-value">{data.estatisticas_medias.kills}</p>
                  <p className="app__stat-key">Kills</p>
                </div>
                <div className="app__stat">
                  <p className="app__stat-value">
                    {data.estatisticas_medias.assists}
                  </p>
                  <p className="app__stat-key">Assists</p>
                </div>
                <div className="app__stat">
                  <p className="app__stat-value">
                    {data.estatisticas_medias.vision}
                  </p>
                  <p className="app__stat-key">Visão</p>
                </div>
              </div>
            </div>
          </div>
        </section>
      )}
    </main>
  );
}

export default App;
