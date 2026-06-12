interface WelcomeProps {
  onUploadClick: () => void;
}

export default function Welcome({ onUploadClick }: WelcomeProps) {
  return (
    <div className="welcome">
      <div className="welcome-inner">
        <div className="welcome-icon">
          <svg width="56" height="56" viewBox="0 0 24 24" fill="none" stroke="#D4AF37"
               strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 2L2 7l10 5 10-5-10-5z"/>
            <path d="M2 17l10 5 10-5"/>
            <path d="M2 12l10 5 10-5"/>
          </svg>
        </div>
        <h1 className="welcome-title">二进制分析控制台</h1>
        <p className="welcome-desc">
          上传一个 x86 Linux ELF 二进制文件，开始逆向分析与反编译。
        </p>
        <div className="welcome-features">
          <div className="feature-card">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                 strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="16 18 22 12 16 6"/>
              <polyline points="8 6 2 12 8 18"/>
            </svg>
            <span>反汇编 & 反编译</span>
          </div>
          <div className="feature-card">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                 strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
            </svg>
            <span>漏洞扫描 & 二进制补丁</span>
          </div>
          <div className="feature-card">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                 strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <rect x="2" y="3" width="20" height="14" rx="2" ry="2"/>
              <line x1="8" y1="21" x2="16" y2="21"/>
              <line x1="12" y1="17" x2="12" y2="21"/>
            </svg>
            <span>GDB 动态调试</span>
          </div>
          <div className="feature-card">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                 strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10"/>
              <line x1="12" y1="16" x2="12" y2="12"/>
              <line x1="12" y1="8" x2="12.01" y2="8"/>
            </svg>
            <span>Ghidra + radare2 工具链</span>
          </div>
        </div>
      </div>
    </div>
  );
}
