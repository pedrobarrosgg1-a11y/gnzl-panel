import { useEffect, useState } from "react";
import { NavLink, Outlet, useLocation } from "react-router";

import { Brand } from "../components/Brand";
import { MenuIcon, XIcon } from "../components/icons";
import { useSystemConfig } from "../hooks/useSystemConfig";
import styles from "./AppLayout.module.css";

const NAV_ITEMS = [
  { to: "/", label: "busca", end: true },
  { to: "/listas", label: "listas", end: false },
  { to: "/lotes", label: "lotes", end: false },
  { to: "/links", label: "links", end: false },
];

const SOON_ITEMS = [
  { label: "dashboard", phase: "fase 2" },
  { label: "metas", phase: "fase 2" },
  { label: "vídeos", phase: "fase 3" },
  { label: "templates", phase: "fase 3" },
];

function SystemStatus() {
  const { status, config } = useSystemConfig();

  if (status === "loading") {
    return (
      <div className={styles.status} role="status">
        <span
          className={`gz-ping gz-ping--pulse ${styles.statusPing}`}
          aria-hidden="true"
        />
        <span>conectando à api</span>
      </div>
    );
  }

  if (status === "error" || !config) {
    return (
      <div className={styles.status}>
        <span className={styles.statusOff} aria-hidden="true" />
        <span>api offline</span>
      </div>
    );
  }

  return (
    <div className={styles.footerGroup}>
      <div className={styles.status}>
        <span className={`gz-ping ${styles.statusPing}`} aria-hidden="true" />
        <span>{config.is_demo ? "modo demo" : "modo shopee"}</span>
      </div>
      <span className={styles.version}>v{config.version}</span>
    </div>
  );
}

export function AppLayout() {
  const [menuOpen, setMenuOpen] = useState(false);
  const location = useLocation();

  useEffect(() => {
    setMenuOpen(false);
  }, [location.pathname]);

  useEffect(() => {
    if (!menuOpen) {
      return;
    }
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setMenuOpen(false);
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [menuOpen]);

  const closeMenu = () => setMenuOpen(false);

  return (
    <div className={styles.shell}>
      <a className={styles.skip} href="#conteudo">
        ir para o conteúdo
      </a>

      {menuOpen ? (
        <button
          type="button"
          className={styles.backdrop}
          aria-label="fechar menu"
          onClick={closeMenu}
        />
      ) : null}

      <aside
        id="app-sidebar"
        className={`${styles.sidebar} ${menuOpen ? styles.sidebarOpen : ""}`}
      >
        <div className={styles.sidebarTop}>
          <Brand onNavigate={closeMenu} />
          <button
            type="button"
            className={styles.closeButton}
            onClick={closeMenu}
            aria-label="fechar menu"
          >
            <XIcon className={styles.menuIcon} />
          </button>
        </div>

        <nav className={styles.nav} aria-label="navegação principal">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                isActive ? `${styles.link} ${styles.linkActive}` : styles.link
              }
            >
              {({ isActive }) => (
                <>
                  <span
                    className={`gz-ping ${styles.navPing} ${
                      isActive ? "" : styles.navPingHidden
                    }`}
                    aria-hidden="true"
                  />
                  {item.label}
                </>
              )}
            </NavLink>
          ))}
        </nav>

        <section className={styles.soon} aria-label="funcionalidades em breve">
          <span className="gz-label">em breve</span>
          <ul className={styles.soonList}>
            {SOON_ITEMS.map((item) => (
              <li key={item.label} className={styles.soonItem}>
                <span>{item.label}</span>
                <span className={styles.phase}>{item.phase}</span>
              </li>
            ))}
          </ul>
        </section>

        <div className={styles.footer}>
          <SystemStatus />
        </div>
      </aside>

      <div className={styles.main}>
        <div className={styles.mobileBar}>
          <Brand onNavigate={closeMenu} />
          <button
            type="button"
            className={styles.menuButton}
            onClick={() => setMenuOpen(true)}
            aria-expanded={menuOpen}
            aria-controls="app-sidebar"
            aria-label="abrir menu"
          >
            <MenuIcon className={styles.menuIcon} />
          </button>
        </div>

        <main className={styles.content} id="conteudo">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
