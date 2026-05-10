import { useState, useEffect } from "react";


const CONFIG_PERFIL_CAMPEAO = {
  corteBaixo: 4,
  corteMedio: 7,
  escalaMax: 10,
  rotulos: {
    baixo: "Baixo",
    medio: "Médio",
    alto: "Alto",
  },
};

function perfilCampeaoEmTexto(valor) {
  const v = Number(valor);
  if (Number.isNaN(v)) return "—";
  const { corteBaixo, corteMedio, rotulos } = CONFIG_PERFIL_CAMPEAO;
  if (v < corteBaixo) return rotulos.baixo;
  if (v < corteMedio) return rotulos.medio;
  return rotulos.alto;
}

function perfilCampeaoPct(valor) {
  const v = Number(valor);
  const max = CONFIG_PERFIL_CAMPEAO.escalaMax;
  if (Number.isNaN(v) || max <= 0) return 0;
  return Math.min(100, Math.max(0, (v / max) * 100));
}

function getDominantStat(perfil) {
  if (!perfil) return null;

  const stats = {
    attack: Number(perfil.attack),
    defense: Number(perfil.defense),
    magic: Number(perfil.magic),
  };

  const validEntries = Object.entries(stats).filter(
    ([, value]) => !Number.isNaN(value)
  );

  if (validEntries.length === 0) return null;

  validEntries.sort((a, b) => b[1] - a[1]);

  return validEntries[0][0];
}

function PerfilStatBlock({ legenda, valor, destacado }) {
  const texto = perfilCampeaoEmTexto(valor);
  const pct = perfilCampeaoPct(valor);
  const v = Number(valor);
  const temNum = !Number.isNaN(v);
  const arred = temNum ? Math.round(v * 10) / 10 : 0;
  const labelAria = temNum
    ? `${legenda}: ${v.toFixed(1)} de ${CONFIG_PERFIL_CAMPEAO.escalaMax}`
    : `${legenda}: indisponível`;

  const [dominantReady, setDominantReady] = useState(() => !destacado);

  useEffect(() => {
    if (!destacado) {
      setDominantReady(false);
      return;
    }
    const reduceMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)"
    ).matches;
    if (reduceMotion) {
      setDominantReady(true);
      return;
    }
    setDominantReady(false);
    const id = window.setTimeout(() => setDominantReady(true), 40);
    return () => window.clearTimeout(id);
  }, [destacado, valor]);

  const [ready, setReady] = useState(false);

  useEffect(() => {
    const reduceMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)"
    ).matches;

    if (reduceMotion) {
      setReady(true);
      return;
    }

    setReady(false);
    const id = window.setTimeout(() => setReady(true), 40);

    return () => window.clearTimeout(id);
  }, [valor]);

  const fillPct = ready ? pct : 0;
  const dominantClass = destacado
    ? `app__stat app__stat--perfil app__stat--dominant-magic${dominantReady ? " app__stat--dominant-magic--ready" : ""
    }`
    : "app__stat app__stat--perfil";

  return (
    <div className={dominantClass}>
      <div className="app__stat-value-wrap">
        <p className="app__stat-value app__stat-value--with-bar">{texto}</p>
        <div
          className="app__stat-progress-track"
          role="progressbar"
          aria-valuemin={0}
          aria-valuemax={CONFIG_PERFIL_CAMPEAO.escalaMax}
          aria-valuenow={arred}
          aria-label={labelAria}
        >
          <div
            className="app__stat-progress-fill"
            style={{ width: `${fillPct}%` }}
          />
        </div>
      </div>
      <p className="app__stat-key">{legenda}</p>
    </div>
  );
}

function tagsParaLista(tags) {
  return String(tags ?? "")
    .split(",")
    .map((t) => t.trim())
    .filter(Boolean);
}

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
  const tagsDoCampeaoAtual = campeaoAtual
    ? tagsParaLista(campeaoAtual.tags)
    : [];
  const dominantStat = getDominantStat(data?.perfil_medio);

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
    <>
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

                        <p className="app__champ-meta app__champ-meta--tags">
                          <strong>Tags:</strong>
                          <span className="app__champ-tag-list" role="list">
                            {tagsDoCampeaoAtual.length === 0 ? (
                              <span
                                className="app__champ-tag app__champ-tag--empty"
                                role="listitem"
                              >
                                —
                              </span>
                            ) : (
                              tagsDoCampeaoAtual.map((tag, i) => (
                                <span
                                  key={`${tag}-${i}`}
                                  className="app__champ-tag"
                                  role="listitem"
                                >
                                  {tag}
                                </span>
                              ))
                            )}
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
                  <h2 className="app__invoker">{data.invocador} #{data.tag_nome}</h2>
                  <span className="app__badge">
                    {(data.rotas_favoritas ?? []).join(", ")}
                  </span>
                </div>

                <p className="app__section-label">Perfil Médio</p>
                <div className="app__stats">
                  <PerfilStatBlock
                    legenda="Ataque AD"
                    valor={data.perfil_medio.attack}
                    destacado={dominantStat === "attack"}
                  />

                  <PerfilStatBlock
                    legenda="Defesa"
                    valor={data.perfil_medio.defense}
                    destacado={dominantStat === "defense"}
                  />

                  <PerfilStatBlock
                    legenda="Ataque AP"
                    valor={data.perfil_medio.magic}
                    destacado={dominantStat === "magic"}
                  />
                </div>

                <p className="app__section-label">Estatísticas médias</p>
                <div className="app__stats">
                  <div className="app__stat">
                    <p className="app__stat-value">{data.perfil_medio.media_kills}</p>
                    <p className="app__stat-key">Kills</p>
                  </div>
                  <div className="app__stat">
                    <p className="app__stat-value">
                      {data.perfil_medio.media_assists}
                    </p>
                    <p className="app__stat-key">Assistencias</p>
                  </div>
                  <div className="app__stat">
                    <p className="app__stat-value">
                      {data.perfil_medio.media_visao}
                    </p>
                    <p className="app__stat-key">Visao</p>
                  </div>
                </div>
              </div>
            </div>
          </section>
        )}
      </main>

      <footer className="app__footer" role="contentinfo">
        <div className="app__footer-inner">
          <p className="app__footer-line">
            <span className="app__footer-brand">LolRecomender</span>
            <span className="app__footer-dot" aria-hidden="true">
              ·
            </span>
            © {new Date().getFullYear()}
          </p>
          <p className="app__footer-legal">
            League of Legends e Riot Games são marcas registradas da Riot
            Games, Inc. Este projeto não é afiliado, patrocinado ou endossado
            pela Riot Games.
          </p>
        </div>
      </footer>
    </>
  );
}

export default App;
