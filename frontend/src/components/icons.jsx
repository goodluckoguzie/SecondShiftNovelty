function Svg({ children }) {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden>
      {children}
    </svg>
  );
}

export function IconMic() {
  return (
    <Svg>
      <rect x="9" y="3" width="6" height="11" rx="3" />
      <path d="M5 11a7 7 0 0 0 14 0" />
      <path d="M12 18v3" />
    </Svg>
  );
}

export function IconList() {
  return (
    <Svg>
      <path d="M8 7h12M8 12h12M8 17h12" />
      <circle cx="4" cy="7" r="1" fill="currentColor" />
      <circle cx="4" cy="12" r="1" fill="currentColor" />
      <circle cx="4" cy="17" r="1" fill="currentColor" />
    </Svg>
  );
}

export function IconFlag() {
  return (
    <Svg>
      <path d="M5 21V4h9l-1.5 4L14 12H5" />
    </Svg>
  );
}

export function IconFile() {
  return (
    <Svg>
      <path d="M7 3h8l5 5v13H7z" />
      <path d="M15 3v5h5" />
    </Svg>
  );
}
