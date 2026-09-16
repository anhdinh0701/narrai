const API_URL = (window.location.port === "3000" || window.location.protocol === "file:")
    ? "http://localhost:8000/api"
    : (window.location.hostname.includes("vercel.app")
        ? "https://narrai-2.onrender.com/api"
        : "/api");

let globalData = {
    initialPrompt: "",
    chatHistory: [],
    refinedPrompt: "",
    sessionId: null,
    storyId: null,
    selectedLength: "medium"
};

// =================== i18n (ĐA NGÔN NGỮ) ===================
const i18nDict = {
    vi: {
        not_logged_in: "Chưa đăng nhập",
        login: "Đăng nhập",
        logout: "Đăng xuất",
        new_story: "Viết truyện mới",
        story_history: "Lịch sử truyện",
        step1_title: "Khởi nguồn ý tưởng",
        genres_label: "Thể loại truyện (Chọn nhiều):",
        themes_label: "Chủ đề thịnh hành (Mix nhiều chủ đề):",
        prompt_placeholder: "Ví dụ: Một thế giới nơi phép thuật bị cấm đoán...",
        continue_btn: "Tiếp tục",
        step2_title: "Xây dựng Nền tảng Cốt truyện",
        chat_placeholder: "Nhập câu trả lời của bạn... (Bấm Enter để gửi)",
        send_btn: "Gửi",
        skip_chat_btn: "Bỏ qua hỏi đáp, Chốt dàn ý luôn",
        step3_title: "Chốt cấu hình & Viết truyện",
        len_short: "Truyện ngắn (500-800 từ)",
        len_medium: "Tiểu thuyết vừa (1500-2500 từ)",
        len_long: "Dài kỳ (3000-5000 từ)",
        start_writing_btn: "Bắt đầu sáng tác",
        editor_title: "Bản Thảo Đang Viết...",
        words: "từ",
        download_btn: "Tải EPUB/PDF",
        editor_placeholder: "Câu chuyện sẽ xuất hiện ở đây. Bạn có thể tự gõ thêm bất cứ lúc nào...",
        tool_rewrite: "Viết lại",
        tool_expand: "Mở rộng",
        tool_shorten: "Rút gọn",
        tool_ai: "Tùy chỉnh với AI",
        ai_copilot: "Trợ lý của bạn",
        ai_welcome_1: "Chào mừng bạn đến với không gian làm việc chuyên nghiệp.",
        tip: "<b>Mẹo:</b>",
        ai_welcome_2: "Trong quá trình viết, hãy bôi đen một đoạn văn chưa ưng ý trong Bản thảo. AI sẽ giúp bạn sửa lại nó ngay lập tức!",
        selected_text: "Đoạn văn đang chọn:",
        ai_instruction_placeholder: "Ví dụ: Đổi giọng văn buồn bã hơn...",
        ai_request_btn: "Yêu cầu AI sửa",
        ai_result: "Kết quả từ AI:",
        accept_btn: "Thay thế",
        reject_btn: "Hủy bỏ",
        ai_thinking: "AI đang suy nghĩ...",
        username: "Tên đăng nhập",
        password: "Mật khẩu",
        no_account: "Chưa có tài khoản?",
        register_now: "Đăng ký ngay",
        has_account: "Đã có tài khoản?",
        login_now: "Đăng nhập ngay",
        register: "Đăng ký",
        loading: "Đang tải...",
        search_genre: "Tìm kiếm thể loại...",
        story_length: "Độ dài truyện",
        creativity: "Độ sáng tạo",
        pacing: "Nhịp độ (Pacing)",
        val_short: "Ngắn", val_med: "Vừa", val_long: "Dài",
        val_logic: "Logic/Thực tế", val_bal: "Cân bằng", val_crazy: "Sáng tạo/Bất ngờ",
        val_slow: "Chậm rãi, Miêu tả kỹ", val_fast: "Nhanh, Kịch tính",
        hero_title: "Khởi Tạo Tác Phẩm Của Bạn Bằng Trí Tuệ Nhân Tạo",
        hero_sub: "Nền tảng Co-creation Workspace hiện đại giúp bạn biến mọi ý tưởng điên rồ nhất thành cuốn tiểu thuyết hoàn chỉnh chỉ trong vài phút.",
        hero_cta: "Bắt đầu sáng tác miễn phí",
        feat1_title: "AI Plot Interview",
        feat1_desc: "Trợ lý AI sẽ phỏng vấn bạn để khai thác và làm chặt chẽ cốt truyện trước khi đặt bút viết.",
        feat2_title: "Interactive Editing",
        feat2_desc: "Bôi đen bất kỳ đoạn văn nào và yêu cầu AI viết lại, mở rộng hoặc tóm lược theo ý muốn.",
        feat3_title: "Đa Ngôn Ngữ",
        feat3_desc: "Hỗ trợ giao diện song ngữ (Anh - Việt) và AI am hiểu văn phong tác giả quốc tế."
    },
    en: {
        not_logged_in: "Not logged in",
        login: "Login",
        logout: "Logout",
        new_story: "New Story",
        story_history: "Story History",
        step1_title: "Idea Generation",
        genres_label: "Genres (Multi-select):",
        themes_label: "Trending Themes (Mix):",
        prompt_placeholder: "Example: A world where magic is forbidden...",
        continue_btn: "Continue",
        step2_title: "Build Story Foundation",
        chat_placeholder: "Type your answer... (Press Enter to send)",
        send_btn: "Send",
        skip_chat_btn: "Skip Q&A, Finalize Outline",
        step3_title: "Configuration & Generation",
        len_short: "Short (500-800 words)",
        len_medium: "Medium (1500-2500 words)",
        len_long: "Long (3000-5000 words)",
        start_writing_btn: "Start Writing",
        editor_title: "Draft in Progress...",
        words: "words",
        download_btn: "Download EPUB/PDF",
        editor_placeholder: "Your story will appear here. You can type freely at any time...",
        tool_rewrite: "Rewrite",
        tool_expand: "Expand",
        tool_shorten: "Shorten",
        tool_ai: "Customize with AI",
        ai_copilot: "AI Assistant",
        ai_welcome_1: "Welcome to your professional workspace.",
        tip: "<b>Tip:</b>",
        ai_welcome_2: "Highlight a paragraph in your draft that you want to change. AI will help you revise it instantly!",
        selected_text: "Selected text:",
        ai_instruction_placeholder: "Example: Make the tone more melancholy...",
        ai_request_btn: "Ask AI to Revise",
        ai_result: "AI Result:",
        accept_btn: "Replace",
        reject_btn: "Cancel",
        ai_thinking: "AI is thinking...",
        username: "Username",
        password: "Password",
        no_account: "Don't have an account?",
        register_now: "Register now",
        has_account: "Already have an account?",
        login_now: "Login now",
        register: "Register",
        loading: "Loading...",
        search_genre: "Search genres...",
        story_length: "Story Length",
        creativity: "Creativity",
        pacing: "Pacing",
        val_short: "Short", val_med: "Medium", val_long: "Long",
        val_logic: "Logical/Realistic", val_bal: "Balanced", val_crazy: "Creative/Unexpected",
        val_slow: "Slow, Descriptive", val_fast: "Fast, Action-packed",
        hero_title: "Generate Your Masterpiece With AI",
        hero_sub: "A modern Co-creation Workspace that turns your wildest ideas into a complete novel in minutes.",
        hero_cta: "Start writing for free",
        feat1_title: "AI Plot Interview",
        feat1_desc: "Our AI assistant will interview you to brainstorm and tighten the plot before writing.",
        feat2_title: "Interactive Editing",
        feat2_desc: "Highlight any paragraph and ask AI to rewrite, expand, or shorten it on the fly.",
        feat3_title: "Multilingual",
        feat3_desc: "Bilingual interface (EN-VI) and an AI that understands world-class authors' writing styles."
    }
};

let currentLang = 'vi';

function setLang(lang) {
    currentLang = lang;
    
    // Update active buttons
    document.getElementById('btnLangVi').classList.remove('active');
    document.getElementById('btnLangEn').classList.remove('active');
    document.getElementById(lang === 'vi' ? 'btnLangVi' : 'btnLangEn').classList.add('active');
    
    // Translate all elements with data-i18n
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        if (i18nDict[lang][key]) {
            el.innerHTML = i18nDict[lang][key];
        }
    });

    // Translate all placeholders with data-i18n-placeholder
    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
        const key = el.getAttribute('data-i18n-placeholder');
        if (i18nDict[lang][key]) {
            el.setAttribute('placeholder', i18nDict[lang][key]);
        }
    });
    
    // Re-render dynamic content
    if(typeof filterGenres === 'function') filterGenres();
    if(typeof fetchTrendingTopics === 'function') fetchTrendingTopics();
    
    // Update sliders
    if(typeof updateLenLabel === 'function') {
        updateLenLabel();
        updateCreativityLabel();
        updatePacingLabel();
    }
    
    // Also re-render history if it's open
    const historyModal = document.getElementById('historyModal');
    if (historyModal && historyModal.style.display === 'block') {
        openHistory();
    }
}


// =================== AUTHENTICATION ===================
let isLoginMode = true;

function authHeaders() {
    const token = localStorage.getItem('narrai_token');
    if (token) return { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` };
    return { 'Content-Type': 'application/json' };
}

async function checkAuth() {
    // Check URL parameters for OAuth redirect first
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.has('access_token')) {
        localStorage.setItem('narrai_token', urlParams.get('access_token'));
        if (urlParams.has('refresh_token')) {
            localStorage.setItem('narrai_refresh_token', urlParams.get('refresh_token'));
        }
    } else if (urlParams.has('auth_error')) {
        const errType = urlParams.get('auth_error');
        const p = urlParams.get('provider') || 'Google';
        const pName = p === 'x' ? 'X' : (p.charAt(0).toUpperCase() + p.slice(1));
        let msg = currentLang === 'vi' 
            ? `Cổng đăng nhập ${pName} chưa được cấu hình Client ID / Secret trên server.` 
            : `${pName} login is not configured with Client ID / Secret on server.`;
        if (errType !== 'provider_not_configured') {
            msg = currentLang === 'vi' ? 'Đăng nhập mạng xã hội thất bại hoặc bị hủy!' : 'Social login failed or cancelled!';
        }
        window.history.replaceState({}, document.title, window.location.pathname);
        openAuthModal();
        const errEl = document.getElementById('authError');
        if (errEl) {
            errEl.textContent = msg;
            errEl.style.color = '#EF4444';
        }
    }

    const token = localStorage.getItem('narrai_token');
    if (token) {
        try {
            const res = await fetch(`${API_URL}/me`, { headers: authHeaders() });
            if (res.ok) {
                const data = await res.json();
                const displayName = data.name || data.username || data.email;
                document.getElementById('welcomeUser').textContent = currentLang === 'vi' ? `Chào, ${displayName}` : `Hi, ${displayName}`;
                document.getElementById('loginBtnSidebar').style.display = 'none';
                document.getElementById('logoutBtnSidebar').style.display = 'block';
                
                // Show App, Hide Landing
                document.getElementById('landingContainer').style.display = 'none';
                document.getElementById('appContainer').style.display = 'flex';
                const wsBg = document.getElementById('workspaceBgStage');
                if (wsBg) wsBg.style.display = 'block';
                const bg = document.getElementById('mangaCinemaBg');
                if (bg) bg.style.display = 'none';
                stopMangaCinema();
                if (typeof BackgroundManager !== 'undefined') BackgroundManager.setContext('setup');
                return;
            } else if (res.status === 401) {
                // Try refresh token if available
                const refreshToken = localStorage.getItem('narrai_refresh_token');
                if (refreshToken) {
                    try {
                        const refreshRes = await fetch(`${API_URL}/refresh`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ refresh_token: refreshToken })
                        });
                        if (refreshRes.ok) {
                            const refreshData = await refreshRes.json();
                            localStorage.setItem('narrai_token', refreshData.access_token);
                            if (refreshData.refresh_token) {
                                localStorage.setItem('narrai_refresh_token', refreshData.refresh_token);
                            }
                            return checkAuth(); // retry with refreshed token
                        }
                    } catch (e) {
                        console.error('Refresh token failed:', e);
                    }
                }
                logout(); // invalid token and refresh failed
            }
        } catch (e) {
            console.error(e);
        }
    }
    document.getElementById('welcomeUser').textContent = i18nDict[currentLang]['not_logged_in'];
    document.getElementById('loginBtnSidebar').style.display = 'block';
    document.getElementById('logoutBtnSidebar').style.display = 'none';
    
    // Show Landing, Hide App
    document.getElementById('landingContainer').style.display = 'block';
    document.getElementById('appContainer').style.display = 'none';
    const wsBg = document.getElementById('workspaceBgStage');
    if (wsBg) wsBg.style.display = 'none';
    const bg = document.getElementById('mangaCinemaBg');
    if (bg) bg.style.display = 'block';
    startMangaCinema();
    if (typeof BackgroundManager !== 'undefined') BackgroundManager.setContext('home');
}

async function logout() {
    const token = localStorage.getItem('narrai_token');
    if (token) {
        try {
            await fetch(`${API_URL}/logout`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${token}` },
            });
        } catch (e) { /* server unreachable — still log out client side */ }
    }
    localStorage.removeItem('narrai_token');
    localStorage.removeItem('narrai_refresh_token');
    checkAuth();
}

// ==========================================================================
// DYNAMIC BACKGROUND MANAGER (MULTI-GENRE & CONTEXT ENGINE)
// ==========================================================================
const BackgroundManager = {
    currentContext: 'home',
    currentGenre: null,
    activeLayer: 'A',
    previewTimer: null,
    lastImageUrl: '',

    // Curated manga / comic visual identity assets
    assets: {
        // Contextual defaults (from Step 1 onwards)
        home: 'assets/manga/page_blue_cinematic.jpg',
        setup: 'assets/manga/page_village_blue_moon.jpg',     // Step 1: Misty blue village under moon
        interview: 'assets/manga/page_ancient_town_rain.jpg', // Step 2: Ancient tiled-roof town in rain
        config: 'assets/manga/page_warrior_canyon_fire.jpg',  // Step 3: Warrior on cliff overlooking glowing canyon
        editor: 'assets/manga/page_moonlit_forest_rain.jpg',  // Editor (Prose): Moonlit rainy forest
        comic: 'assets/manga/page_comic_action_full.png',     // Comic mode: Action comic full page
        history: 'assets/manga/page_manga_detective_full.png',

        // Genres
        xianxia: 'assets/manga/page_warrior_canyon_fire.jpg',
        wuxia: 'assets/manga/panel_sword_mountain.jpg',
        fantasy: 'assets/manga/page_village_blue_moon.jpg',
        action: 'assets/manga/panel_combat_punch.jpg',
        romance: 'assets/manga/panel_two_detectives.jpg',
        mystery: 'assets/manga/page_ancient_town_rain.jpg',
        urban: 'assets/manga/panel_city_window.jpg',
        scifi: 'assets/manga/panel_blue_glowing_eyes.jpg',
        adventure: 'assets/manga/page_moonlit_forest_rain.jpg',
        horror: 'assets/manga/page_rain_forest_silhouette.png',
        manga: 'assets/manga/page_manga_detective_full.png'
    },

    init() {
        this.preload([
            this.assets.setup,
            this.assets.interview,
            this.assets.config,
            this.assets.editor,
            this.assets.comic,
            this.assets.xianxia,
            this.assets.fantasy,
            this.assets.action,
            this.assets.romance,
            this.assets.mystery
        ]);
    },

    preload(urls) {
        if (!Array.isArray(urls)) return;
        urls.forEach(url => {
            if (!url) return;
            const img = new Image();
            img.src = url;
        });
    },

    setContext(contextName) {
        this.currentContext = contextName;
        const stage = document.getElementById('workspaceBgStage');
        if (contextName === 'home') {
            if (stage) stage.style.display = 'none';
            return;
        }
        if (stage) stage.style.display = 'block';
        if ((contextName === 'setup' || contextName === 'editor') && this.currentGenre && this.assets[this.currentGenre]) {
            this.transitionTo(this.assets[this.currentGenre]);
            return;
        }
        const targetImg = this.assets[contextName] || this.assets.setup;
        this.transitionTo(targetImg);
    },

    setGenre(genreKey) {
        this.currentGenre = genreKey;
        const targetImg = (genreKey && this.assets[genreKey]) || this.assets[this.currentContext] || this.assets.setup;
        this.transitionTo(targetImg);
    },

    previewGenre(genreKey) {
        clearTimeout(this.previewTimer);
        const targetImg = this.assets[genreKey];
        if (targetImg && targetImg !== this.lastImageUrl) {
            this.transitionTo(targetImg, 0.95);
        }
    },

    restoreGenre() {
        clearTimeout(this.previewTimer);
        this.previewTimer = setTimeout(() => {
            if (this.currentGenre && this.assets[this.currentGenre]) {
                this.transitionTo(this.assets[this.currentGenre], 0.92);
            } else {
                this.setContext(this.currentContext);
            }
        }, 280);
    },

    transitionTo(imageUrl, targetOpacity = 0.92) {
        if (!imageUrl || imageUrl === this.lastImageUrl) return;
        this.lastImageUrl = imageUrl;

        const layerA = document.getElementById('wsBgLayerA');
        const layerB = document.getElementById('wsBgLayerB');
        if (!layerA || !layerB) return;

        const nextLayer = this.activeLayer === 'A' ? layerB : layerA;
        const prevLayer = this.activeLayer === 'A' ? layerA : layerB;

        const tempImg = new Image();
        tempImg.onload = () => {
            nextLayer.style.backgroundImage = `url('${imageUrl}')`;
            nextLayer.style.opacity = targetOpacity;
            nextLayer.classList.add('active');

            prevLayer.style.opacity = '0';
            prevLayer.classList.remove('active');

            this.activeLayer = this.activeLayer === 'A' ? 'B' : 'A';
        };
        tempImg.onerror = () => {
            nextLayer.style.backgroundImage = `url('assets/manga/page_village_blue_moon.jpg')`;
            nextLayer.style.opacity = targetOpacity;
            nextLayer.classList.add('active');
            prevLayer.style.opacity = '0';
            prevLayer.classList.remove('active');
            this.activeLayer = this.activeLayer === 'A' ? 'B' : 'A';
        };
        tempImg.src = imageUrl;
    }
};

// ==========================================================================
// CINEMATIC ANIMATED MANGA BACKGROUND CONTROLLER
// ==========================================================================
let mangaCinemaActive = false;
let mangaSlideTimer = null;
let mangaCurrentSlide = 0;
let mangaRafId = null;
let mangaMouseX = 0;
let mangaMouseY = 0;
let mangaTargetX = 0;
let mangaTargetY = 0;
let mangaParallaxBound = false;

function initMangaCinema() {
    if (mangaParallaxBound) return;
    mangaParallaxBound = true;

    // Smooth desktop mouse-tracking for subtle parallax
    window.addEventListener('mousemove', (e) => {
        if (!mangaCinemaActive || window.innerWidth <= 768) return;
        const cx = window.innerWidth / 2;
        const cy = window.innerHeight / 2;
        mangaTargetX = Math.max(-1, Math.min(1, (e.clientX - cx) / cx));
        mangaTargetY = Math.max(-1, Math.min(1, (e.clientY - cy) / cy));
    }, { passive: true });

    // Close on Escape key
    window.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && mangaCinemaActive) {
            closeAuthModal();
        }
    });

    // Close on background backdrop click
    const modalEl = document.getElementById('authModal');
    if (modalEl) {
        modalEl.addEventListener('click', (e) => {
            if (e.target === modalEl) {
                closeAuthModal();
            }
        });
    }
}

function startMangaCinema() {
    initMangaCinema();
    mangaCinemaActive = true;
    
    // Start background crossfade sequence between manga panels (every 8.5 seconds)
    const slides = document.querySelectorAll('#cinemaBgLayer .cinema-slide');
    if (slides && slides.length > 1) {
        clearInterval(mangaSlideTimer);
        mangaSlideTimer = setInterval(() => {
            if (!mangaCinemaActive) return;
            slides[mangaCurrentSlide].classList.remove('active');
            mangaCurrentSlide = (mangaCurrentSlide + 1) % slides.length;
            slides[mangaCurrentSlide].classList.add('active');
        }, 8500);
    }

    // Start mouse parallax RAF loop on desktop
    if (window.innerWidth > 768 && !('ontouchstart' in window)) {
        cancelAnimationFrame(mangaRafId);
        function parallaxLoop() {
            if (!mangaCinemaActive) return;
            // Smooth linear interpolation (lerp)
            mangaMouseX += (mangaTargetX - mangaMouseX) * 0.08;
            mangaMouseY += (mangaTargetY - mangaMouseY) * 0.08;

            document.documentElement.style.setProperty('--bg-offset-x', `${(mangaMouseX * 22).toFixed(2)}px`);
            document.documentElement.style.setProperty('--bg-offset-y', `${(mangaMouseY * 16).toFixed(2)}px`);
            document.documentElement.style.setProperty('--panel-offset-x', `${(mangaMouseX * 20).toFixed(2)}px`);
            document.documentElement.style.setProperty('--panel-offset-y', `${(mangaMouseY * 15).toFixed(2)}px`);

            mangaRafId = requestAnimationFrame(parallaxLoop);
        }
        mangaRafId = requestAnimationFrame(parallaxLoop);
    }
}

function stopMangaCinema() {
    mangaCinemaActive = false;
    clearInterval(mangaSlideTimer);
    mangaSlideTimer = null;
    cancelAnimationFrame(mangaRafId);
    mangaRafId = null;
}

function openAuthModal() {
    const modal = document.getElementById('authModal');
    if (modal) {
        modal.style.display = 'flex';
    }
    const errEl = document.getElementById('authError');
    if (errEl) errEl.textContent = '';
    loadAuthProviders();
    startMangaCinema();
}

function closeAuthModal() {
    const modal = document.getElementById('authModal');
    if (modal) {
        modal.style.display = 'none';
    }
    const landing = document.getElementById('landingContainer');
    if (!landing || landing.style.display === 'none') {
        stopMangaCinema();
    }
}

function toggleAuthMode() {
    isLoginMode = !isLoginMode;
    const title = document.getElementById('authTitle');
    const btn = document.getElementById('authSubmitBtn');
    const toggleTxt = document.getElementById('authToggleText');
    const toggleLink = document.getElementById('authToggleLink');
    
    if (isLoginMode) {
        title.setAttribute('data-i18n', 'login');
        btn.setAttribute('data-i18n', 'login');
        toggleTxt.setAttribute('data-i18n', 'no_account');
        toggleLink.setAttribute('data-i18n', 'register_now');
    } else {
        title.setAttribute('data-i18n', 'register');
        btn.setAttribute('data-i18n', 'register');
        toggleTxt.setAttribute('data-i18n', 'has_account');
        toggleLink.setAttribute('data-i18n', 'login_now');
    }
    setLang(currentLang);
}

async function loadAuthProviders() {
    try {
        const res = await fetch(`${API_URL}/auth/providers`);
        if (res.ok) {
            const data = await res.json();
            const configured = data.providers || [];
            let unconfiguredCount = 0;
            ['google', 'facebook', 'x'].forEach(provider => {
                const btnId = `btn${provider.charAt(0).toUpperCase() + provider.slice(1)}`;
                const btn = document.getElementById(btnId);
                if (btn) {
                    const pName = provider === 'x' ? 'X' : (provider.charAt(0).toUpperCase() + provider.slice(1));
                    if (configured.includes(provider)) {
                        btn.disabled = false;
                        btn.style.opacity = '1';
                        btn.style.cursor = 'pointer';
                        btn.title = `Continue with ${pName}`;
                        btn.onclick = () => socialLogin(provider);
                    } else {
                        unconfiguredCount++;
                        btn.disabled = true;
                        btn.style.opacity = '0.45';
                        btn.style.cursor = 'not-allowed';
                        const notConfigMsg = currentLang === 'vi' 
                            ? `Cổng đăng nhập ${pName} chưa được cấu hình Client ID / Secret trên server.` 
                            : `${pName} login is not configured with Client ID / Secret on server.`;
                        btn.title = notConfigMsg;
                        btn.onclick = (e) => {
                            e.preventDefault();
                            const errEl = document.getElementById('authError');
                            if (errEl) {
                                errEl.textContent = notConfigMsg;
                                errEl.style.color = '#EF4444';
                            }
                        };
                    }
                }
            });

            // Non-blocking notice below social buttons
            const noticeEl = document.getElementById('socialNotice');
            if (noticeEl) {
                if (!configured.includes('google')) {
                    noticeEl.textContent = currentLang === 'vi'
                        ? "Lưu ý: Đăng nhập Google/Mạng xã hội chưa được cấu hình Client ID / Secret trên server."
                        : "Note: Google / Social login is not configured with Client ID / Secret on server.";
                    noticeEl.style.display = 'block';
                } else {
                    noticeEl.style.display = 'none';
                }
            }
        }
    } catch(e) {
        console.warn('Failed to load auth providers:', e);
    }
}

function socialLogin(provider) {
    const btnId = `btn${provider.charAt(0).toUpperCase() + provider.slice(1)}`;
    const btn = document.getElementById(btnId);
    if (btn && btn.disabled) {
        const pName = provider === 'x' ? 'X' : (provider.charAt(0).toUpperCase() + provider.slice(1));
        const errEl = document.getElementById('authError');
        if (errEl) {
            errEl.textContent = currentLang === 'vi'
                ? `Cổng đăng nhập ${pName} chưa được cấu hình Client ID / Secret trên server.`
                : `${pName} login is not configured with Client ID / Secret on server.`;
            errEl.style.color = '#EF4444';
        }
        return;
    }
    window.location.href = `${API_URL}/auth/${provider}`;
}

async function submitAuth() {
    const u = document.getElementById('authUsername').value.trim();
    const p = document.getElementById('authPassword').value.trim();
    const err = document.getElementById('authError');
    err.textContent = '';
    
    if(!u || !p) {
        err.textContent = "Vui lòng nhập đủ thông tin!";
        return;
    }
    
    try {
        if (isLoginMode) {
            const formData = new URLSearchParams();
            formData.append('username', u);
            formData.append('password', p);
            
            const res = await fetch(`${API_URL}/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: formData
            });
            const data = await res.json();
            
            if (res.ok) {
                localStorage.setItem('narrai_token', data.access_token);
                if (data.refresh_token) {
                    localStorage.setItem('narrai_refresh_token', data.refresh_token);
                }
                closeAuthModal();
                checkAuth();
            } else {
                err.textContent = data.detail || "Đăng nhập thất bại";
            }
        } else {
            const isEmail = u.includes('@');
            const res = await fetch(`${API_URL}/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    username: u,
                    password: p,
                    email: isEmail ? u : null
                })
            });
            const data = await res.json();
            
            if (res.ok) {
                alert(currentLang === 'vi' ? "Đăng ký thành công! Hãy đăng nhập." : "Register success! Please login.");
                toggleAuthMode();
            } else {
                err.textContent = data.detail || "Đăng ký thất bại";
            }
        }
    } catch(e) {
        err.textContent = "Lỗi kết nối!";
    }
}



// =================== SWR CACHING ===================
async function fetchWithSWR(cacheKey, url, options, renderCallback) {
    const cached = localStorage.getItem(cacheKey);
    if (cached) {
        try {
            renderCallback(JSON.parse(cached));
        } catch (e) {}
    }
    
    try {
        const response = await fetch(url, options);
        if (response.ok) {
            const data = await response.json();
            if (JSON.stringify(data) !== cached) {
                localStorage.setItem(cacheKey, JSON.stringify(data));
                renderCallback(data);
            }
        } else {
            renderCallback({ status: 'error', message: 'API Error' });
        }
    } catch (e) {
        if (!cached) renderCallback({ status: 'error', message: 'Network Error' });
    }
}

// UI Navigation
function showPhase(phaseNumber) {
    document.querySelectorAll('.phase').forEach(el => el.classList.remove('active'));
    document.getElementById(`phase${phaseNumber}`).classList.add('active');
    if (typeof BackgroundManager !== 'undefined') {
        if (phaseNumber === 1) BackgroundManager.setContext('setup');
        else if (phaseNumber === 2) BackgroundManager.setContext('interview');
        else if (phaseNumber === 3) BackgroundManager.setContext('config');
    }
}

// =================== PHASE 1 & 2: SETUP & INTERVIEW ===================
async function generateQuestions() {
    let prompt = document.getElementById('initialPrompt').value.trim();
    const genres = Array.from(selectedTags).join(", ");
    const themes = Array.from(selectedThemes).join(", ");
    
    let combinedPrompt = prompt;
    if (genres) combinedPrompt = `[Thể loại: ${genres}] ${combinedPrompt}`;
    if (themes) combinedPrompt = `[Chủ đề: ${themes}] ${combinedPrompt}`;

    if (!combinedPrompt) {
        alert("Vui lòng nhập ý tưởng hoặc chọn thể loại!");
        return;
    }

    globalData.initialPrompt = combinedPrompt;
    globalData.chatHistory = [{"role": "user", "content": combinedPrompt}];
    
    showPhase(2);
    const chatBox = document.getElementById('chatBox');
    chatBox.innerHTML = `
        <div class="chat-message chat-user">${combinedPrompt}</div>
        <div class="chat-message chat-ai" id="chatLoading">${i18nDict[currentLang]['ai_thinking']}</div>
    `;

    try {
        const response = await fetch(`${API_URL}/chat-interview`, {
            method: 'POST',
            headers: authHeaders(),
            body: JSON.stringify({ chat_history: globalData.chatHistory })
        });
        const data = await response.json();
        
        document.getElementById('chatLoading').remove();
        
        if (data.status === 'success') {
            globalData.chatHistory.push({"role": "assistant", "content": data.message});
            chatBox.innerHTML += `<div class="chat-message chat-ai">${formatAIResponse(data.message)}</div>`;
            
            if (data.is_ready) forceRefinePrompt();
        } else {
            throw new Error(data.message);
        }
    } catch (error) {
        document.getElementById('chatLoading').textContent = "Lỗi kết nối.";
    }
}

async function sendChatMessage() {
    const input = document.getElementById('chatInput');
    const msg = input.value.trim();
    if(!msg) return;
    
    input.value = '';
    const chatBox = document.getElementById('chatBox');
    
    globalData.chatHistory.push({"role": "user", "content": msg});
    chatBox.innerHTML += `<div class="chat-message chat-user">${msg}</div>`;
    chatBox.innerHTML += `<div class="chat-message chat-ai" id="chatLoading">${i18nDict[currentLang]['ai_thinking']}</div>`;
    chatBox.scrollTop = chatBox.scrollHeight;

    if (typeof AIStudioChat !== 'undefined') AIStudioChat.setState('thinking');

    try {
        const response = await fetch(`${API_URL}/chat-interview`, {
            method: 'POST',
            headers: authHeaders(),
            body: JSON.stringify({ chat_history: globalData.chatHistory })
        });
        const data = await response.json();
        
        document.getElementById('chatLoading').remove();
        if (typeof AIStudioChat !== 'undefined') AIStudioChat.setState('idle');
        
        if (data.status === 'success') {
            globalData.chatHistory.push({"role": "assistant", "content": data.message});
            chatBox.innerHTML += `<div class="chat-message chat-ai">${formatAIResponse(data.message)}</div>`;
            chatBox.scrollTop = chatBox.scrollHeight;
            
            if (data.is_ready) forceRefinePrompt();
        } else {
            chatBox.innerHTML += `<div class="chat-message chat-ai" style="color:red">Lỗi từ máy chủ: ${data.message}</div>`;
        }
    } catch (error) {
        document.getElementById('chatLoading').textContent = "Lỗi kết nối.";
        if (typeof AIStudioChat !== 'undefined') AIStudioChat.setState('idle');
    }
}

function formatAIResponse(text) {
    return text.replace(/\n/g, '<br>');
}

async function forceRefinePrompt() {
    const chatBox = document.getElementById('chatBox');
    chatBox.innerHTML += `<div class="chat-message chat-ai" style="color:#d97706">${currentLang === 'vi' ? 'Đang chốt dàn ý...' : 'Finalizing outline...'}</div>`;
    chatBox.scrollTop = chatBox.scrollHeight;

    try {
        const response = await fetch(`${API_URL}/refine-prompt`, {
            method: 'POST',
            headers: authHeaders(),
            body: JSON.stringify({ chat_history: globalData.chatHistory })
        });
        const data = await response.json();
        
        if (data.status === 'success') {
            globalData.refinedPrompt = data.refined_prompt;
            showPhase(3);
        }
    } catch (error) {
        alert("Lỗi chốt dàn ý.");
    }
}

// =================== PHASE 3: GENERATE & EDITOR WORKSPACE ===================
async function generateStory() {
    const lenVal = document.getElementById('lengthSlider').value;
    globalData.selectedLength = lenVal == 1 ? 'short' : (lenVal == 2 ? 'medium' : 'long');
    
    const creativity = document.getElementById('creativitySlider').value;
    const pacing = document.getElementById('pacingSlider').value;
    
    let extraPrompt = "";
    if (creativity == 1) extraPrompt += " Hãy giữ cốt truyện cực kỳ logic, thực tế. ";
    else if (creativity == 3) extraPrompt += " Hãy bùng nổ sáng tạo, thêm những tình tiết bất ngờ (plot twist) điên rồ. ";
    
    if (pacing == 1) extraPrompt += " Nhịp độ truyện chậm rãi, miêu tả nội tâm và bối cảnh thật chi tiết. ";
    else if (pacing == 3) extraPrompt += " Nhịp độ truyện nhanh, dồn dập, tập trung vào hành động và hội thoại kịch tính. ";
    
    globalData.finalPromptForGeneration = globalData.refinedPrompt + "\n" + extraPrompt;
    // A new draft must never reuse a long-story session from a previous draft.
    globalData.sessionId = null;
    globalData.storyId = null;
    
    document.getElementById('setupView').style.display = 'none';
    document.getElementById('editorView').style.display = 'block';
    if (typeof BackgroundManager !== 'undefined') BackgroundManager.setContext('editor');
    
    const output = document.getElementById('storyOutput');
    output.innerHTML = `<i>${currentLang==='vi'?'Đang khởi tạo bản thảo...':'Generating draft...'}</i><br><br>`;
    
    try {
        // Use init-story for long stories (memory system), generate-story for short/medium
        const apiEndpoint = globalData.selectedLength === 'long' ? 'init-story' : 'generate-story';
        const response = await fetch(`${API_URL}/${apiEndpoint}`, {
            method: 'POST',
            headers: authHeaders(),
            body: JSON.stringify({
                refined_prompt: globalData.finalPromptForGeneration,
                story_length: globalData.selectedLength
            })
        });
        
        if (!response.ok) throw new Error(`Lỗi server`);
        
        output.innerHTML = '';
        const reader = response.body.getReader();
        const decoder = new TextDecoder("utf-8");
        let fullStory = "";
        
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            const chunk = decoder.decode(value, { stream: true });
            stopLatencySensor();
            fullStory += chunk;
            
            const formattedStory = cleanStreamText(fullStory)
                .split('\n')
                .filter(line => line.trim())
                .map(line => `<p>${line}</p>`)
                .join('');
            
            output.innerHTML = formattedStory;
            updateWordCount();
        }

        const generationError = getStreamError(fullStory);
        if (generationError) {
            output.textContent = generationError;
            output.style.color = '#b91c1c';
            return;
        }

        // Extract session_id if present (from init-story)
        const sessionMatch = fullStory.match(/\[SESSION_ID:([^\]]+)\]/);
        if (sessionMatch) {
            globalData.sessionId = sessionMatch[1];
            // Remove session marker from displayed text
            output.innerHTML = output.innerHTML.replace(/\[SESSION_ID:[^\]]+\]/, '');
            // Show chapter action buttons
            const chatHistory = document.getElementById('chatHistory');
            if (chatHistory) {
                chatHistory.innerHTML += '<div class="chat-message chat-ai">Chuong 1 da hoan tat! Ban co the an "Viet tiep chuong moi" de AI viet tiep, hoac "Ket thuc truyen" de AI viet doan ket.</div>';
            }
        }
        const storyMatch = fullStory.match(/\[STORY_ID:(\d+)\]/);
        if (storyMatch) {
            globalData.storyId = Number(storyMatch[1]);
            output.innerHTML = output.innerHTML.replace(/\[STORY_ID:\d+\]/, '');
        }
    } catch (error) {
        output.textContent = 'Không thể sinh truyện lúc này. Vui lòng thử lại sau.';
        output.style.color = '#b91c1c';
    }
}

function updateWordCount() {
    const text = document.getElementById('storyOutput').innerText;
    const count = text.trim().split(/\s+/).filter(w => w.length > 0).length;
    const label = i18nDict[currentLang]['words'];
    document.getElementById('wordCount').textContent = `${count} ${label}`;
}

function getStreamError(text) {
    const match = text.match(/\[(?:GENERATION_ERROR|Lỗi sinh truyện|Loi sinh truyen|Lỗi|Loi):\s*([\s\S]*?)\]/i);
    return match ? match[1].trim() : null;
}

function cleanStreamText(text) {
    return text
        .replace(/\[(?:GENERATION_ERROR|Lỗi sinh truyện|Loi sinh truyen|Lỗi|Loi):[\s\S]*$/i, '')
        .replace(/\[(?:SESSION_ID|STORY_ID):[^\]]*\]/g, '');
}


// =================== SYSTEM SENSORS ===================
async function sendSystemAlert(eventType, eventData) {
    if (!globalData.sessionId) return;
    
    try {
        const response = await fetch(`${API_URL}/copilot-event`, {
            method: 'POST',
            headers: authHeaders(),
            body: JSON.stringify({
                session_id: globalData.sessionId,
                event_type: eventType,
                event_data: eventData
            })
        });
        
        const data = await response.json();
        if (data.status === 'success') {
            const action = data.data.action;
            const params = data.data.action_params || {};
            
            if (action === 'reply_user') {
                const chatHistory = document.getElementById('chatHistory');
                if (chatHistory) {
                    chatHistory.innerHTML += `<div class="chat-message chat-ai" style="color: #64748b;"><i>[Hệ thống] ${params.message}</i></div>`;
                    chatHistory.scrollTop = chatHistory.scrollHeight;
                }
            } else if (action === 'heal_image') {
                healImagePanel(params.panel_id, params.new_prompt);
            }
        }
    } catch (e) {
        console.error('Lỗi gửi system alert:', e);
    }
}

async function healImagePanel(panelId, newPrompt) {
    const chatHistory = document.getElementById('chatHistory');
    if (chatHistory) {
        chatHistory.innerHTML += `<div class="chat-message chat-ai" style="color: #64748b;"><i>[Hệ thống] Đang vẽ lại khung tranh số ${panelId}...</i></div>`;
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }
    
    const panelImg = document.getElementById('panel-img-' + panelId);
    if (!panelImg) return;
    
    // Xoa onerror de tranh vong lap vo han neu server anh bi sap hoan toan
    panelImg.onerror = null;
    
    // Thu ve lai bang Pollinations voi seed ngau nhien
    const seed = Math.floor(Math.random() * 10000);
    const url = `https://image.pollinations.ai/prompt/${encodeURIComponent(newPrompt)}?width=1024&height=1024&nologo=true&seed=${seed}`;
    panelImg.src = url;
}

// Global Latency Timer
let latencyTimer = null;
function startLatencySensor(operation) {
    clearTimeout(latencyTimer);
    latencyTimer = setTimeout(() => {
        sendSystemAlert('SYS_LATENCY', `Toi dang doi ${operation} qua 15s ma chua thay phan hoi.`);
    }, 15000);
}
function stopLatencySensor() {
    clearTimeout(latencyTimer);
}

// =================== INTERACTIVE EDITING ===================
let currentSelectionRange = null;

document.addEventListener('selectionchange', () => {
    const selection = window.getSelection();
    const toolbar = document.getElementById('floatingToolbar');
    const editor = document.getElementById('storyOutput');
    const mainEditor = document.querySelector('.main-editor');
    
    if (!selection.isCollapsed && editor.contains(selection.anchorNode)) {
        const range = selection.getRangeAt(0);
        const rect = range.getBoundingClientRect();
        const editorRect = mainEditor.getBoundingClientRect();
        
        const topPos = rect.top - editorRect.top + mainEditor.scrollTop - 50;
        const leftPos = rect.left - editorRect.left + mainEditor.scrollLeft + (rect.width / 2);
        
        toolbar.style.display = 'flex';
        toolbar.style.top = `${topPos}px`;
        toolbar.style.left = `${leftPos}px`;
        toolbar.style.transform = 'translate(-50%, -100%)';
        
        currentSelectionRange = range;
    } else {
        toolbar.style.display = 'none';
    }
});

function openAIChatForSelection() {
    document.getElementById('floatingToolbar').style.display = 'none';
    const selectedText = currentSelectionRange.toString();
    
    document.getElementById('aiWelcomeMsg').style.display = 'none';
    document.getElementById('aiResultBox').style.display = 'none';
    
    const box = document.getElementById('aiSelectionBox');
    box.style.display = 'block';
    document.getElementById('aiSelectionText').textContent = selectedText;
    document.getElementById('aiCustomInstruction').value = '';
    document.getElementById('aiCustomInstruction').focus();
}

function interactiveEdit(instruction) {
    document.getElementById('floatingToolbar').style.display = 'none';
    const selectedText = currentSelectionRange.toString();
    
    document.getElementById('aiWelcomeMsg').style.display = 'none';
    document.getElementById('aiSelectionBox').style.display = 'block';
    document.getElementById('aiSelectionText').textContent = selectedText;
    
    // In english mode, translate the prompt slightly
    if(currentLang === 'en') {
        if(instruction.includes('viết lại')) instruction = "Rewrite this beautifully";
        if(instruction.includes('mở rộng')) instruction = "Expand this with more descriptive details";
        if(instruction.includes('tóm lược')) instruction = "Shorten this for faster pacing";
    }
    document.getElementById('aiCustomInstruction').value = instruction;
    
    submitCustomEdit();
}

async function submitCustomEdit() {
    const originalText = document.getElementById('aiSelectionText').textContent;
    const instruction = document.getElementById('aiCustomInstruction').value;
    
    if(!instruction.trim()) return;
    
    document.getElementById('aiSelectionBox').style.display = 'none';
    document.getElementById('aiLoading').style.display = 'block';
    
    try {
        const response = await fetch(`${API_URL}/edit-text`, {
            method: 'POST',
            headers: authHeaders(),
            body: JSON.stringify({
                original_text: originalText,
                instruction: instruction
            })
        });
        const data = await response.json();
        
        document.getElementById('aiLoading').style.display = 'none';
        
        if(data.status === 'success') {
            document.getElementById('aiResultBox').style.display = 'block';
            document.getElementById('aiNewText').innerHTML = data.revised_text.replace(/\n/g, '<br>');
        }
    } catch(e) {
        document.getElementById('aiLoading').style.display = 'none';
        document.getElementById('aiSelectionBox').style.display = 'block';
    }
}

function acceptEdit() {
    const newText = document.getElementById('aiNewText').innerText;
    if (currentSelectionRange) {
        currentSelectionRange.deleteContents();
        currentSelectionRange.insertNode(document.createTextNode(newText));
        document.getElementById('aiResultBox').style.display = 'none';
        document.getElementById('aiWelcomeMsg').style.display = 'block';
        updateWordCount();
    }
}

function rejectEdit() {
    document.getElementById('aiResultBox').style.display = 'none';
    document.getElementById('aiWelcomeMsg').style.display = 'block';
}

// =================== INIT & MISC ===================
let selectedTags = new Set();
let selectedThemes = new Set();
const allGenres = [
    // Nhóm 1: Tình cảm
    { vi: "Ngôn tình", en: "Romance", img: "assets/manga/panel_two_detectives.jpg", bg: "romance" },
    { vi: "Đam mỹ", en: "Boys' Love (BL)", img: "assets/manga/panel_two_detectives.jpg", bg: "romance" },
    { vi: "Bách hợp", en: "Girls' Love (GL)", img: "assets/manga/panel_woman.jpg", bg: "romance" },
    { vi: "Thanh xuân", en: "School Life", img: "assets/manga/panel_detective_coffee.jpg", bg: "romance" },
    { vi: "Cưới trước yêu sau", en: "Arranged Marriage", img: "assets/manga/panel_two_detectives.jpg", bg: "romance" },
    // Nhóm 2: Kỳ ảo
    { vi: "Tiên hiệp", en: "Xianxia", img: "assets/manga/page_warrior_canyon_fire.jpg", bg: "xianxia" },
    { vi: "Kiếm hiệp", en: "Wuxia", img: "assets/manga/panel_sword_mountain.jpg", bg: "wuxia" },
    { vi: "Huyền huyễn", en: "Xuanhuan", img: "assets/manga/page_village_blue_moon.jpg", bg: "fantasy" },
    { vi: "Kỳ ảo", en: "Fantasy", img: "assets/manga/page_village_blue_moon.jpg", bg: "fantasy" },
    { vi: "Khoa học viễn tưởng", en: "Sci-Fi", img: "assets/manga/panel_blue_glowing_eyes.jpg", bg: "scifi" },
    { vi: "Xuyên không", en: "Isekai", img: "assets/manga/page_village_blue_moon.jpg", bg: "fantasy" },
    { vi: "Trọng sinh", en: "Rebirth", img: "assets/manga/panel_blue_hero_profile.jpg", bg: "fantasy" },
    { vi: "Hệ thống", en: "System", img: "assets/manga/panel_blue_glowing_eyes.jpg", bg: "scifi" },
    { vi: "Mạt thế", en: "Post-Apocalyptic", img: "assets/manga/panel_combat_punch.jpg", bg: "action" },
    // Nhóm 3: Hành động
    { vi: "Hành động", en: "Action", img: "assets/manga/panel_combat_punch.jpg", bg: "action" },
    { vi: "Phiêu lưu", en: "Adventure", img: "assets/manga/page_moonlit_forest_rain.jpg", bg: "adventure" },
    { vi: "Võng du", en: "LitRPG", img: "assets/manga/panel_combat_punch.jpg", bg: "action" },
    // Nhóm 4: Bí ẩn
    { vi: "Trinh thám", en: "Mystery", img: "assets/manga/page_ancient_town_rain.jpg", bg: "mystery" },
    { vi: "Kinh dị", en: "Horror", img: "assets/manga/page_rain_forest_silhouette.png", bg: "horror" },
    { vi: "Giật gân", en: "Thriller", img: "assets/manga/page_rain_forest_silhouette.png", bg: "horror" },
    { vi: "Linh dị", en: "Supernatural", img: "assets/manga/panel_hands_book.jpg", bg: "horror" },
    // Nhóm 5: Đời sống
    { vi: "Đô thị", en: "Urban", img: "assets/manga/panel_city_window.jpg", bg: "urban" },
    { vi: "Điền văn", en: "Slice of Life", img: "assets/manga/page_ancient_town_rain.jpg", bg: "urban" },
    { vi: "Hài hước", en: "Comedy", img: "assets/manga/panel_detective_coffee.jpg", bg: "manga" },
    { vi: "Bi kịch", en: "Tragedy", img: "assets/manga/panel_blue_hero_cloak.jpg", bg: "fantasy" },
    { vi: "Lịch sử", en: "Historical", img: "assets/manga/panel_sword_mountain.jpg", bg: "wuxia" },
    { vi: "Cung đấu", en: "Palace Scheme", img: "assets/manga/panel_woman.jpg", bg: "romance" }
];

function initGenres(filterText = "") {
    const genresContainer = document.getElementById('genresContainer');
    if (!genresContainer) return;
    genresContainer.innerHTML = '';

    allGenres.forEach(genre => {
        const textToDisplay = currentLang === 'vi' ? genre.vi : genre.en;
        const searchBase = (genre.vi + " " + genre.en).toLowerCase();

        if (filterText && !searchBase.includes(filterText.toLowerCase())) {
            return; // skip if doesn't match search
        }

        const isSelected = selectedTags.has(genre.vi);
        const card = document.createElement('div');
        card.className = `genre-card${isSelected ? ' selected' : ''}`;
        card.setAttribute('data-genre', genre.vi);
        card.setAttribute('title', textToDisplay);

        card.innerHTML = `
            <img src="${genre.img}" alt="${textToDisplay}" class="genre-card-img" loading="lazy" onerror="this.src='assets/manga/panel_street_mountain.jpg'" />
            <div class="genre-card-overlay">
                <span class="genre-card-title">${textToDisplay}</span>
            </div>
            <div class="genre-card-badge">✓</div>
        `;

        card.onclick = (e) => {
            e.preventDefault();
            const nowSelected = !selectedTags.has(genre.vi);
            if (nowSelected) {
                selectedTags.add(genre.vi);
                card.classList.add('selected');
                if (typeof BackgroundManager !== 'undefined') BackgroundManager.setGenre(genre.bg);
            } else {
                selectedTags.delete(genre.vi);
                card.classList.remove('selected');
                if (typeof BackgroundManager !== 'undefined') {
                    const remaining = Array.from(selectedTags);
                    if (remaining.length > 0) {
                        const lastGenre = allGenres.find(g => g.vi === remaining[remaining.length - 1]);
                        if (lastGenre) BackgroundManager.setGenre(lastGenre.bg);
                    } else {
                        BackgroundManager.setGenre(null);
                    }
                }
            }
        };

        card.onmouseenter = () => {
            if (typeof BackgroundManager !== 'undefined') BackgroundManager.previewGenre(genre.bg);
        };

        card.onmouseleave = () => {
            if (typeof BackgroundManager !== 'undefined') BackgroundManager.restoreGenre();
        };

        genresContainer.appendChild(card);
    });
}

function filterGenres() {
    const searchVal = document.getElementById('genreSearch').value;
    initGenres(searchVal);
}

async function fetchTrendingTopics() {
    try {
        const mockData = [
            { title: { vi: "Chữa lành & Bỏ phố về quê", en: "Healing & Rural Life" } },
            { title: { vi: "Trùng sinh báo thù & Nữ cường", en: "Rebirth & Strong Female Lead" } },
            { title: { vi: "Cưới trước yêu sau / Hợp đồng hôn nhân", en: "Contract Marriage & Romance" } },
            { title: { vi: "Linh dị dân gian Việt Nam", en: "Folk Horror & Mystery" } },
            { title: { vi: "Xuyên thư & Hệ thống 'Vô tri'", en: "Transmigration & Goofy System" } },
            { title: { vi: "Thanh xuân vườn trường & Tình đầu", en: "School Life & First Love" } },
            { title: { vi: "Drama công sở & Gen Z đi làm", en: "Office Drama & Gen Z" } }
        ];
        
        const trendingContainer = document.getElementById('trendingContainer');
        if (!trendingContainer) return;
        trendingContainer.innerHTML = '';
        
        mockData.forEach(topic => {
            const textToDisplay = currentLang === 'vi' ? topic.title.vi : topic.title.en;
            const tag = document.createElement('div');
            tag.className = 'trending-tag';
            if (selectedThemes.has(topic.title.vi)) tag.classList.add('selected-tag');
            tag.textContent = textToDisplay;
            tag.onclick = (e) => {
                e.preventDefault();
                tag.classList.toggle('selected-tag');
                if (selectedThemes.has(topic.title.vi)) selectedThemes.delete(topic.title.vi);
                else selectedThemes.add(topic.title.vi);
            };
            trendingContainer.appendChild(tag);
        });
    } catch (error) {
        console.error(error);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    if (typeof BackgroundManager !== 'undefined') {
        BackgroundManager.init();
    }
    if (typeof AIStudioChat !== 'undefined') {
        AIStudioChat.init();
    }
    startMangaCinema();
    initGenres();
    setLang(currentLang);
    checkAuth();
    loadStabilityConfig();
    
    // Add Enter key listeners
    const chatInput = document.getElementById('chatInput');
    if (chatInput) {
        chatInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendChatMessage(); }
        });
    }

    const chatInputText = document.getElementById('chatInputText');
    if (chatInputText) {
        chatInputText.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendAssistantMessage(); }
        });
    }
    
    const aiCustomInput = document.getElementById('aiCustomInstruction');
    if (aiCustomInput) {
        aiCustomInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); submitCustomEdit(); }
        });
    }
});

function downloadStory() {
    const storyText = document.getElementById('storyOutput').innerText;
    const element = document.createElement('a');
    element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(storyText));
    element.setAttribute('download', 'ban-thao.txt');
    element.style.display = 'none';
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
}

// Modal History
function renderHistoryList(data) {
    const list = document.getElementById('historyList');
    if(data.status === 'success') {
        if(data.stories.length === 0) {
            list.innerHTML = `<p style="text-align:center; color:#777; margin-top:20px;">${currentLang === 'vi' ? 'Bạn chưa tạo truyện nào.' : 'No stories found.'}</p>`;
            return;
        }
        list.innerHTML = '';
        data.stories.forEach(s => {
            const item = document.createElement('div');
            item.className = 'history-item';
            item.innerHTML = `
                <div class="history-title">${s.title}</div>
                <div class="history-meta">${s.created_at} &bull; ${s.word_count} ${i18nDict[currentLang]['words']}</div>
                <div class="history-snippet">${s.snippet}</div>
            `;
            item.onclick = () => loadStory(s.id);
            list.appendChild(item);
        });
    } else {
        list.innerHTML = `<p style="color:red;">${data.message}</p>`;
    }
}

async function openHistory() { 
    document.getElementById('historyModal').style.display = 'block'; 
    if (typeof BackgroundManager !== 'undefined') BackgroundManager.setContext('history');
    const list = document.getElementById('historyList');
    list.innerHTML = i18nDict[currentLang]['loading'];
    
    // Apply SWR
    fetchWithSWR('cache_stories', `${API_URL}/stories`, { headers: authHeaders() }, renderHistoryList);
}

function closeHistory() { 
    document.getElementById('historyModal').style.display = 'none'; 
    if (typeof BackgroundManager !== 'undefined') {
        const isEditor = document.getElementById('editorView') && document.getElementById('editorView').style.display === 'block';
        const isComic = document.getElementById('comicView') && document.getElementById('comicView').style.display === 'block';
        BackgroundManager.setContext(isComic ? 'comic' : (isEditor ? 'editor' : 'setup'));
    }
}
window.onclick = function(event) { 
    if (event.target == document.getElementById('historyModal')) closeHistory(); 
    if (event.target == document.getElementById('authModal')) closeAuthModal(); 
}

function renderStoryDetail(data) {
    const output = document.getElementById('storyOutput');
    if(data.status === 'success') {
        globalData.sessionId = null;
        globalData.storyId = null;
        const formattedStory = (data.story.story_content || '')
            .split('\n')
            .filter(line => line.trim())
            .map(line => `<p>${line}</p>`)
            .join('');
        output.innerHTML = formattedStory;
        updateWordCount();
        
        // Restore session state
        if (data.story.session_id) {
            globalData.sessionId = data.story.session_id;
        }
        globalData.storyId = data.story.id || null;
        if (data.story.refined_prompt) {
            globalData.refinedPrompt = data.story.refined_prompt;
        }
    } else {
        output.innerHTML = `<p style="color:red;">${data.message}</p>`;
    }
}

async function loadStory(id) {
    closeHistory();
    document.getElementById('setupView').style.display = 'none';
    document.getElementById('editorView').style.display = 'block';
    if (typeof BackgroundManager !== 'undefined') BackgroundManager.setContext('editor');
    
    const output = document.getElementById('storyOutput');
    output.innerHTML = `<div class="ai-loading">${i18nDict[currentLang]['loading']}</div>`;
    
    fetchWithSWR(`cache_story_${id}`, `${API_URL}/stories/${id}`, { headers: authHeaders() }, renderStoryDetail);
}

// SLIDERS LOGIC
function updateLenLabel() {
    const val = document.getElementById('lengthSlider').value;
    const label = document.getElementById('lenLabel');
    if (val == 1) label.innerText = "Dưới 5000 từ (Chương tiêu chuẩn)";
    else if (val == 2) label.innerText = "5000 - 6000 từ (Chương dài)";
    else label.innerText = "Trên 10.000 từ (Tiểu thuyết)";
}
function updateCreativityLabel() {
    const val = document.getElementById('creativitySlider').value;
    const label = document.getElementById('creativityLabel');
    if(val == 1) label.innerText = i18nDict[currentLang]['val_logic'];
    else if(val == 2) label.innerText = i18nDict[currentLang]['val_bal'];
    else label.innerText = i18nDict[currentLang]['val_crazy'];
}
function updatePacingLabel() {
    const val = document.getElementById('pacingSlider').value;
    const label = document.getElementById('pacingLabel');
    if(val == 1) label.innerText = i18nDict[currentLang]['val_slow'];
    else if(val == 2) label.innerText = i18nDict[currentLang]['val_bal'];
    else label.innerText = i18nDict[currentLang]['val_fast'];
}

// =================== STABILITY AI & COMIC GENERATION ===================
let lastComicText = "";
let hasGeneratedComic = false;
let currentEnhancementMode = "none";
let currentEnhancementStrength = 0.35;
let stabilityConfigLoaded = false;

async function loadStabilityConfig() {
    try {
        const [stabRes, comfyRes] = await Promise.allSettled([
            fetch(`${API_URL}/stability/config`),
            fetch(`${API_URL}/comfy/status`)
        ]);

        let stabEnabled = false;
        if (stabRes.status === 'fulfilled' && stabRes.value.ok) {
            const data = await stabRes.value.json();
            if (data.status === 'success') {
                stabilityConfigLoaded = true;
                stabEnabled = !!data.enabled;
                if (data.default_mode) {
                    setEnhancementMode(data.default_mode);
                }
            }
        }

        let comfyText = "ComfyUI: Ngoại tuyến";
        if (comfyRes.status === 'fulfilled' && comfyRes.value.ok) {
            const cData = await comfyRes.value.json();
            if (cData.connected) {
                const ckptName = (cData.checkpoint || "Model").replace(".safetensors", "");
                comfyText = `ComfyUI: ${ckptName} (Đã kết nối)`;
            } else if (cData.comfyui_online) {
                comfyText = "ComfyUI: Đang tải Model";
            }
        }

        const stabText = stabEnabled ? "Stability AI: Sẵn sàng" : "Stability AI: Tắt";
        const statusEl = document.getElementById('enhancementStatusText');
        if (statusEl) {
            statusEl.innerText = `${comfyText} | ${stabText}`;
        }
    } catch (err) {
        console.warn("Could not fetch pipeline config:", err);
    }
}

function setEnhancementMode(mode) {
    currentEnhancementMode = mode;
    document.querySelectorAll('#enhancementModeGroup .mode-toggle-btn').forEach(btn => {
        btn.classList.toggle('active', btn.getAttribute('data-mode') === mode);
    });
    const strContainer = document.getElementById('strengthContainer');
    if (strContainer) {
        strContainer.style.display = (mode === 'enhance') ? 'flex' : 'none';
    }
}

function updateEnhancementStrengthLabel(val) {
    currentEnhancementStrength = parseFloat(val);
    const lbl = document.getElementById('strengthValueLabel');
    if (lbl) lbl.innerText = currentEnhancementStrength.toFixed(2);
}

function switchPanelStage(panelDiv, stage) {
    const img = panelDiv.querySelector('.panel-img-wrap img');
    if (!img) return;

    let targetUrl = '';
    if (stage === 'final') {
        targetUrl = panelDiv.dataset.finalUrl || panelDiv.dataset.originalUrl;
    } else if (stage === 'processed') {
        targetUrl = panelDiv.dataset.processedUrl || panelDiv.dataset.finalUrl;
    } else if (stage === 'original') {
        targetUrl = panelDiv.dataset.originalUrl;
    }

    if (targetUrl) {
        img.src = targetUrl;
        panelDiv.querySelectorAll('.panel-stage-switch .stage-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.stage === stage);
        });
    }
}

async function onDemandEnhance(panelDiv, mode) {
    const panelId = panelDiv.dataset.panelId;
    if (!panelId) {
        alert('Không tìm thấy mã khung tranh để xử lý.');
        return;
    }

    const imgWrap = panelDiv.querySelector('.panel-img-wrap');
    const actionBtns = panelDiv.querySelectorAll('.panel-action-btn');
    actionBtns.forEach(b => b.disabled = true);

    let overlay = imgWrap.querySelector('.panel-enhancing-overlay');
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.className = 'panel-enhancing-overlay';
        imgWrap.appendChild(overlay);
    }
    overlay.style.display = 'flex';
    const modeLabel = mode === 'upscale' ? 'Đang phóng to & tăng nét 4x qua Stability AI...' : 'Đang tối ưu chi tiết & ánh sáng qua Stability AI...';
    overlay.innerHTML = `<span>${modeLabel}</span><small style="color:#94a3b8; margin-top:4px;">Vui lòng đợi giây lát</small>`;

    try {
        const res = await fetch(`${API_URL}/comic/enhance-panel`, {
            method: 'POST',
            headers: authHeaders(),
            body: JSON.stringify({
                panel_id: parseInt(panelId, 10),
                mode: mode,
                strength: currentEnhancementStrength
            })
        });

        const data = await res.json();
        overlay.style.display = 'none';
        actionBtns.forEach(b => b.disabled = false);

        if (res.ok && data.status === 'success' && data.panel) {
            const p = data.panel;
            panelDiv.dataset.processedUrl = p.processed_image_url || '';
            panelDiv.dataset.finalUrl = p.final_image_url || p.image_url;
            if (p.original_image_url) {
                panelDiv.dataset.originalUrl = p.original_image_url;
            }

            const img = imgWrap.querySelector('img');
            if (img) {
                img.src = p.final_image_url || p.image_url;
            }

            const stageSwitch = panelDiv.querySelector('.panel-stage-switch');
            if (stageSwitch) {
                stageSwitch.innerHTML = '';
                const finalBtn = document.createElement('button');
                finalBtn.className = 'stage-btn active';
                finalBtn.dataset.stage = 'final';
                finalBtn.innerText = 'Bản cuối';
                finalBtn.onclick = () => switchPanelStage(panelDiv, 'final');
                stageSwitch.appendChild(finalBtn);

                if (p.processed_image_url) {
                    const procBtn = document.createElement('button');
                    procBtn.className = 'stage-btn';
                    procBtn.dataset.stage = 'processed';
                    procBtn.innerText = 'Nâng cao';
                    procBtn.onclick = () => switchPanelStage(panelDiv, 'processed');
                    stageSwitch.appendChild(procBtn);
                }

                if (p.original_image_url) {
                    const origBtn = document.createElement('button');
                    origBtn.className = 'stage-btn';
                    origBtn.dataset.stage = 'original';
                    origBtn.innerText = 'Bản gốc';
                    origBtn.onclick = () => switchPanelStage(panelDiv, 'original');
                    stageSwitch.appendChild(origBtn);
                }
            }

            const tag = panelDiv.querySelector('.panel-provider-tag');
            if (tag) {
                tag.innerText = mode === 'upscale' ? 'Stability AI 4x' : 'Stability AI Chi tiết';
            }
        } else {
            alert(data.message || 'Lỗi khi xử lý nâng cao tranh.');
        }
    } catch (err) {
        overlay.style.display = 'none';
        actionBtns.forEach(b => b.disabled = false);
        alert(`Lỗi kết nối máy chủ: ${err.message}`);
    }
}

async function onDemandComfyUIGenerate(panelDiv) {
    const panelId = panelDiv.dataset.panelId;
    if (!panelId) {
        alert('Không tìm thấy mã khung tranh.');
        return;
    }

    const imgWrap = panelDiv.querySelector('.panel-img-wrap');
    const actionBtns = panelDiv.querySelectorAll('.panel-action-btn');
    actionBtns.forEach(b => b.disabled = true);

    let overlay = imgWrap.querySelector('.panel-enhancing-overlay');
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.className = 'panel-enhancing-overlay';
        imgWrap.appendChild(overlay);
    }
    overlay.style.display = 'flex';
    overlay.innerHTML = `<span>Đang kết nối ComfyUI kết xuất lại khung tranh...</span><small style="color:#94a3b8; margin-top:4px;">Thời gian dự kiến ~15 giây</small>`;

    try {
        const res = await fetch(`${API_URL}/comic/generate-comfyui-panel`, {
            method: 'POST',
            headers: authHeaders(),
            body: JSON.stringify({
                panel_id: parseInt(panelId, 10),
                prompt: panelDiv.dataset.prompt || ''
            })
        });

        const data = await res.json();
        overlay.style.display = 'none';
        actionBtns.forEach(b => b.disabled = false);

        if (res.ok && data.status === 'success' && data.panel) {
            const p = data.panel;
            panelDiv.dataset.finalUrl = p.final_image_url || p.image_url;
            panelDiv.dataset.originalUrl = p.original_image_url || p.image_url;
            panelDiv.dataset.processedUrl = '';

            const img = imgWrap.querySelector('img');
            if (img) {
                img.src = p.final_image_url || p.image_url;
            }

            const stageSwitch = panelDiv.querySelector('.panel-stage-switch');
            if (stageSwitch) {
                stageSwitch.innerHTML = '';
                const finalBtn = document.createElement('button');
                finalBtn.className = 'stage-btn active';
                finalBtn.dataset.stage = 'final';
                finalBtn.innerText = 'Bản gốc (ComfyUI)';
                finalBtn.onclick = () => switchPanelStage(panelDiv, 'final');
                stageSwitch.appendChild(finalBtn);
            }

            const tag = panelDiv.querySelector('.panel-provider-tag');
            if (tag) {
                tag.innerText = 'ComfyUI';
            }
        } else {
            alert(data.message || 'Lỗi khi tạo lại bằng ComfyUI.');
        }
    } catch (err) {
        overlay.style.display = 'none';
        actionBtns.forEach(b => b.disabled = false);
        alert(`Lỗi kết nối ComfyUI: ${err.message}`);
    }
}

function renderComicPanel(p, index, grid) {
    const panelDiv = document.createElement('div');
    panelDiv.className = `comic-panel panel-${p.layout_type || 'square'}`;
    panelDiv.id = `panel-card-${p.id || index}`;

    panelDiv.dataset.finalUrl = p.final_image_url || p.image_url || '';
    panelDiv.dataset.processedUrl = p.processed_image_url || '';
    panelDiv.dataset.originalUrl = p.original_image_url || p.image_url || '';
    panelDiv.dataset.panelId = p.id || '';
    panelDiv.dataset.prompt = p.image_prompt || '';

    // Header bar (Badge hidden per user request)
    const headerBar = document.createElement('div');
    headerBar.className = 'panel-header-bar';

    const stageSwitch = document.createElement('div');
    stageSwitch.className = 'panel-stage-switch';

    function createStageBtn(stage, label, isActive) {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = `stage-btn ${isActive ? 'active' : ''}`;
        btn.dataset.stage = stage;
        btn.innerText = label;
        btn.onclick = () => switchPanelStage(panelDiv, stage);
        return btn;
    }

    stageSwitch.appendChild(createStageBtn('final', 'Bản cuối', true));
    if (p.processed_image_url) {
        stageSwitch.appendChild(createStageBtn('processed', 'Nâng cao', false));
    }
    if (p.original_image_url) {
        stageSwitch.appendChild(createStageBtn('original', 'Bản gốc', false));
    }
    headerBar.appendChild(stageSwitch);
    panelDiv.appendChild(headerBar);

    // Image wrapper
    const imgWrap = document.createElement('div');
    imgWrap.className = 'panel-img-wrap';

    const skeleton = document.createElement('div');
    skeleton.className = 'comic-panel-skeleton';
    skeleton.innerHTML = '<span style="color:#64748b; font-size:0.85rem">Đang tải ảnh...</span>';
    imgWrap.appendChild(skeleton);

    const img = document.createElement('img');
    img.alt = p.image_prompt || 'Comic Panel';
    img.style.display = 'none';

    img.onload = () => {
        skeleton.style.display = 'none';
        img.style.display = 'block';
        img.classList.add('loaded');
    };

    let retryCount = 0;
    img.onerror = () => {
        const currentSrc = img.src || '';
        if (retryCount < 1 && currentSrc.startsWith('http')) {
            retryCount += 1;
            const retrySeed = Math.floor(Math.random() * 100000);
            const sep = currentSrc.includes('?') ? '&' : '?';
            img.src = `${currentSrc}${sep}retry=${retrySeed}`;
            return;
        }
        skeleton.innerHTML = '<span style="color:#ef4444; font-size:0.8rem; padding:15px; text-align:center;">Không tải được ảnh.<br><small>Hãy thử lại sau.</small></span>';
    };

    img.src = p.final_image_url || p.image_url;
    imgWrap.appendChild(img);
    panelDiv.appendChild(imgWrap);

    // Panel action bar (on-demand ComfyUI re-render, enhance & upscale buttons)
    const actionBar = document.createElement('div');
    actionBar.className = 'panel-action-bar';

    const btnGroup = document.createElement('div');
    btnGroup.className = 'panel-action-btn-group';

    const comfyBtn = document.createElement('button');
    comfyBtn.type = 'button';
    comfyBtn.className = 'panel-action-btn';
    comfyBtn.innerText = 'Vẽ lại bằng ComfyUI';
    comfyBtn.onclick = () => onDemandComfyUIGenerate(panelDiv);
    btnGroup.appendChild(comfyBtn);

    const upscaleBtn = document.createElement('button');
    upscaleBtn.type = 'button';
    upscaleBtn.className = 'panel-action-btn';
    upscaleBtn.innerText = 'Tăng nét 4x';
    upscaleBtn.onclick = () => onDemandEnhance(panelDiv, 'upscale');
    btnGroup.appendChild(upscaleBtn);

    const enhanceBtn = document.createElement('button');
    enhanceBtn.type = 'button';
    enhanceBtn.className = 'panel-action-btn';
    enhanceBtn.innerText = 'Tối ưu chi tiết';
    enhanceBtn.onclick = () => onDemandEnhance(panelDiv, 'enhance');
    btnGroup.appendChild(enhanceBtn);

    actionBar.appendChild(btnGroup);

    const tag = document.createElement('span');
    tag.className = 'panel-provider-tag';
    if (p.enhancement_provider === 'stability-ai') {
        tag.innerText = p.enhancement_mode === 'upscale' ? 'Stability AI 4x' : 'Stability AI Chi tiết';
    } else {
        tag.innerText = 'ComfyUI Gốc';
    }
    actionBar.appendChild(tag);
    panelDiv.appendChild(actionBar);

    // Manga Speech Bubble Overlay (Bong bóng thoại hình oval đứng)
    if (p.dialogue_text) {
        const overlay = document.createElement('div');
        overlay.className = 'manga-bubble-overlay';
        const defaultPos = (index % 2 === 0) ? 'manga-pos-bottom-left' : 'manga-pos-bottom-right';

        const bubble = document.createElement('div');
        bubble.className = `manga-bubble ${defaultPos} bubble-speech`;

        const body = document.createElement('div');
        body.className = 'manga-bubble-body';

        const textEl = document.createElement('div');
        textEl.className = 'manga-bubble-text';
        textEl.contentEditable = 'true';
        textEl.spellcheck = false;
        textEl.title = 'Bấm trực tiếp để chỉnh sửa lời thoại';
        textEl.innerText = p.dialogue_text;
        body.appendChild(textEl);
        bubble.appendChild(body);

        const actions = document.createElement('div');
        actions.className = 'manga-bubble-actions';
        actions.innerHTML = `
            <button type="button" class="mb-act-btn" title="Đổi góc đặt bóng thoại" onclick="cycleBubblePos(this)">⇄ Vị trí</button>
            <button type="button" class="mb-act-btn" title="Đổi kiểu bóng (Nói / Hét / Nghĩ / Thì thầm)" onclick="cycleBubbleType(this)">💭 Kiểu</button>
            <button type="button" class="mb-act-btn btn-del" title="Xóa bóng thoại" onclick="deleteBubble(this)">✕</button>
        `;
        bubble.appendChild(actions);
        overlay.appendChild(bubble);
        imgWrap.appendChild(overlay);
    }

    grid.appendChild(panelDiv);
}

// ============================================================
// NARRAI PRO — Progress UI Helpers
// ============================================================

const PRO_STEPS = ['pstep-analyze', 'pstep-story', 'pstep-chars', 'pstep-panels', 'pstep-art', 'pstep-finish'];

function proSetStep(stepId, state) {
    const el = document.getElementById(stepId);
    if (!el) return;
    el.className = `pro-step ${state}`;
}

function proAdvanceProgress(doneUpTo) {
    PRO_STEPS.forEach((id, i) => {
        if (i < doneUpTo) proSetStep(id, 'done');
        else if (i === doneUpTo) proSetStep(id, 'active');
        else proSetStep(id, 'pending');
    });
    const pct = Math.round((doneUpTo / (PRO_STEPS.length - 1)) * 100);
    const bar = document.getElementById('proProgressBar');
    if (bar) bar.style.width = `${pct}%`;
}

function proResetProgress() {
    PRO_STEPS.forEach(id => proSetStep(id, 'pending'));
    const bar = document.getElementById('proProgressBar');
    if (bar) bar.style.width = '0%';
}

function proCompleteProgress() {
    PRO_STEPS.forEach(id => proSetStep(id, 'done'));
    const bar = document.getElementById('proProgressBar');
    if (bar) bar.style.width = '100%';
}

// ============================================================
// NARRAI PRO — Character-Specific Speech Bubble Compositor
// ============================================================

function getSpeakerBadgeClass(speaker) {
    const s = (speaker || '').toLowerCase();
    if (s.includes('dẫn') || s.includes('narrat') || s.includes('người kể')) {
        return 'speaker-narrator';
    }
    if (s.includes('linh') || s.includes('nữ') || s.includes('muội') || s.includes('cô') || s.includes('bạch')) {
        return 'speaker-companion';
    }
    if (s.includes('ma') || s.includes('quỷ') || s.includes('địch') || s.includes('thú') || s.includes('sát')) {
        return 'speaker-villain';
    }
    return 'speaker-hero';
}

function getPanelClassByLayout(p, index) {
    if (p.layout_type === 'wide') return 'pro-panel-wide';
    if (p.layout_type === 'tall') return 'pro-panel-tall';
    // Dynamic paneling rhythm based on storyboard pacing
    if (index === 0) return 'pro-panel-wide'; // Establishing scene
    if (index % 4 === 1) return 'pro-panel-focus';
    if (index % 4 === 2) return 'pro-panel-close';
    if (index % 4 === 3) return 'pro-panel-half';
    return 'pro-panel-half';
}

function getShotTypeLabel(p, index) {
    const st = ((p.shot_type || p.camera_angle || '') + '').toLowerCase();
    if (st.includes('wide') || p.layout_type === 'wide') return 'ĐẠI CẢNH (WIDE)';
    if (st.includes('tall') || st.includes('action') || p.layout_type === 'tall') return 'HÀNH ĐỘNG (ACTION)';
    if (st.includes('close')) return 'CẬN CẢNH (CLOSE-UP)';
    if (st.includes('two')) return 'ĐỐI THOẠI (TWO-SHOT)';
    if (index === 0) return 'MỞ ĐẦU (ESTABLISHING)';
    return 'TRUNG CẢNH (MEDIUM)';
}

function renderProComicPanel(p, index, container) {
    const panelWrap = document.createElement('div');
    const layoutClass = getPanelClassByLayout(p, index);
    panelWrap.className = `pro-panel ${layoutClass}`;
    const panelId = `pro-panel-${p.id || index}`;
    panelWrap.id = panelId;

    const inner = document.createElement('div');
    inner.className = 'pro-panel-inner';

    // 1. Image Box / Manga Panel Container
    const imgBox = document.createElement('div');
    imgBox.className = 'pro-panel-img-box manga-panel-container';

    // Top Header Bar: Quick Manga Tools (Badge hidden per user request)
    const topbar = document.createElement('div');
    topbar.className = 'manga-panel-topbar';

    const tools = document.createElement('div');
    tools.className = 'manga-panel-tools';

    const addBubbleBtn = document.createElement('button');
    addBubbleBtn.type = 'button';
    addBubbleBtn.className = 'manga-tool-btn';
    addBubbleBtn.innerHTML = '+ Thoại';
    addBubbleBtn.title = 'Thêm bong bóng thoại vào khung tranh';
    addBubbleBtn.onclick = (e) => { e.stopPropagation(); addBubbleToPanel(panelId); };
    tools.appendChild(addBubbleBtn);

    const regenBtn = document.createElement('button');
    regenBtn.type = 'button';
    regenBtn.className = 'manga-tool-btn';
    regenBtn.innerHTML = '🎨 Vẽ lại';
    regenBtn.title = 'Làm mới khung hình';
    regenBtn.onclick = (e) => { e.stopPropagation(); regenPanelImage(panelId); };
    tools.appendChild(regenBtn);

    topbar.appendChild(tools);
    imgBox.appendChild(topbar);

    // Narration banner overlay inside panel if present
    if (p.narration && p.narration.trim().length > 0) {
        const narBanner = document.createElement('div');
        narBanner.className = 'manga-narration-banner';
        narBanner.contentEditable = 'true';
        narBanner.spellcheck = false;
        narBanner.title = 'Bấm để chỉnh sửa lời dẫn';
        narBanner.textContent = p.narration;
        imgBox.appendChild(narBanner);
    }

    // Skeleton loader
    const skeleton = document.createElement('div');
    skeleton.className = 'pro-panel-skeleton';
    skeleton.innerHTML = '<span style="color:#64748b;font-size:0.75rem;">Đang kết xuất tranh AI...</span>';
    imgBox.appendChild(skeleton);

    // Image element
    const img = document.createElement('img');
    img.alt = p.image_prompt || `Khung tranh ${p.panel_index || index + 1}`;
    img.style.display = 'none';

    img.onload = () => {
        skeleton.style.display = 'none';
        img.style.display = 'block';
    };

    let retries = 0;
    img.onerror = () => {
        const src = img.src || '';
        if (retries < 1 && src.startsWith('http')) {
            retries++;
            img.src = src + (src.includes('?') ? '&' : '?') + 'r=' + Date.now();
            return;
        }
        skeleton.innerHTML = '<span style="color:#ef4444;font-size:0.75rem;padding:10px;">Không tải được ảnh</span>';
    };

    img.src = p.final_image_url || p.image_url || '';
    imgBox.appendChild(img);

    // 2. Manga Speech Bubbles Overlay
    const overlay = document.createElement('div');
    overlay.className = 'manga-bubble-overlay';

    const dialogueText = (p.dialogue_text || p.dialogue || '').trim();
    if (dialogueText.length > 0) {
        const speakerName = p.speaker || 'Nhân vật';
        const speakerBadgeClass = getSpeakerBadgeClass(speakerName);
        const bType = p.bubble_type || 'speech';
        const defaultPos = (index % 2 === 0) ? 'manga-pos-bottom-left' : 'manga-pos-bottom-right';

        const bubble = document.createElement('div');
        bubble.className = `manga-bubble ${defaultPos} bubble-${bType}`;

        // Character name tag hidden per user request

        const body = document.createElement('div');
        body.className = 'manga-bubble-body';

        const textEl = document.createElement('div');
        textEl.className = 'manga-bubble-text';
        textEl.contentEditable = 'true';
        textEl.spellcheck = false;
        textEl.title = 'Bấm trực tiếp để chỉnh sửa lời thoại';
        textEl.textContent = dialogueText;
        body.appendChild(textEl);
        bubble.appendChild(body);

        const actions = document.createElement('div');
        actions.className = 'manga-bubble-actions';
        actions.innerHTML = `
            <button type="button" class="mb-act-btn" title="Đổi góc đặt bóng thoại" onclick="cycleBubblePos(this)">⇄ Vị trí</button>
            <button type="button" class="mb-act-btn" title="Đổi kiểu bóng (Nói / Hét / Nghĩ / Thì thầm)" onclick="cycleBubbleType(this)">💭 Kiểu</button>
            <button type="button" class="mb-act-btn btn-del" title="Xóa bóng thoại" onclick="deleteBubble(this)">✕</button>
        `;
        bubble.appendChild(actions);
        overlay.appendChild(bubble);
    }

    imgBox.appendChild(overlay);
    inner.appendChild(imgBox);

    panelWrap.appendChild(inner);
    container.appendChild(panelWrap);
}

// Interactive Manga Speech Bubble Helpers
function cycleBubblePos(btn) {
    const bubble = btn.closest('.manga-bubble');
    if (!bubble) return;
    const positions = ['manga-pos-bottom-left', 'manga-pos-bottom-right', 'manga-pos-top-right', 'manga-pos-top-left'];
    const currentPos = positions.find(p => bubble.classList.contains(p)) || positions[0];
    bubble.classList.remove(currentPos);
    const nextPos = positions[(positions.indexOf(currentPos) + 1) % positions.length];
    bubble.classList.add(nextPos);
}

function cycleBubbleType(btn) {
    const bubble = btn.closest('.manga-bubble');
    if (!bubble) return;
    const types = ['bubble-speech', 'bubble-shout', 'bubble-thought', 'bubble-narration', 'bubble-whisper'];
    const currentType = types.find(t => bubble.classList.contains(t)) || types[0];
    bubble.classList.remove(currentType);
    const nextType = types[(types.indexOf(currentType) + 1) % types.length];
    bubble.classList.add(nextType);
}

function cycleSpeakerTag(tagEl) {
    const tags = ['speaker-hero', 'speaker-companion', 'speaker-villain', 'speaker-narrator'];
    const currentTag = tags.find(t => tagEl.classList.contains(t)) || tags[0];
    tagEl.classList.remove(currentTag);
    const nextTag = tags[(tags.indexOf(currentTag) + 1) % tags.length];
    tagEl.classList.add(nextTag);
}

function deleteBubble(btn) {
    const bubble = btn.closest('.manga-bubble');
    if (bubble) bubble.remove();
}

function addBubbleToPanel(panelWrapId) {
    const panelWrap = document.getElementById(panelWrapId);
    if (!panelWrap) return;
    let overlay = panelWrap.querySelector('.manga-bubble-overlay');
    if (!overlay) {
        const container = panelWrap.querySelector('.manga-panel-container') || panelWrap;
        overlay = document.createElement('div');
        overlay.className = 'manga-bubble-overlay';
        container.appendChild(overlay);
    }
    const bubble = document.createElement('div');
    bubble.className = 'manga-bubble manga-pos-bottom-right bubble-speech';
    bubble.innerHTML = `
        <div class="manga-bubble-body">
            <div class="manga-bubble-text" contenteditable="true" spellcheck="false" title="Bấm để chỉnh sửa lời thoại">Nhập lời thoại mới...</div>
        </div>
        <div class="manga-bubble-actions">
            <button type="button" class="mb-act-btn" title="Đổi góc đặt bóng thoại" onclick="cycleBubblePos(this)">⇄ Vị trí</button>
            <button type="button" class="mb-act-btn" title="Đổi kiểu bóng (Nói / Hét / Nghĩ / Thì thầm)" onclick="cycleBubbleType(this)">💭 Kiểu</button>
            <button type="button" class="mb-act-btn btn-del" title="Xóa bóng thoại" onclick="deleteBubble(this)">✕</button>
        </div>
    `;
    overlay.appendChild(bubble);
    const textEl = bubble.querySelector('.manga-bubble-text');
    if (textEl) {
        textEl.focus();
        const range = document.createRange();
        range.selectNodeContents(textEl);
        const sel = window.getSelection();
        sel.removeAllRanges();
        sel.addRange(range);
    }
}

function regenPanelImage(panelWrapId) {
    const panelWrap = document.getElementById(panelWrapId);
    if (!panelWrap) return;
    const img = panelWrap.querySelector('img');
    const skeleton = panelWrap.querySelector('.pro-panel-skeleton');
    if (img && skeleton) {
        skeleton.style.display = 'flex';
        skeleton.innerHTML = '<span style="color:#38bdf8;font-size:0.75rem;">Đang làm mới tranh...</span>';
        img.style.display = 'none';
        const currentSrc = img.src.split('?')[0];
        img.src = `${currentSrc}?t=${Date.now()}`;
        img.onload = () => {
            skeleton.style.display = 'none';
            img.style.display = 'block';
        };
    }
}

// Bind to window for HTML inline calls
window.cycleBubblePos = cycleBubblePos;
window.cycleBubbleType = cycleBubbleType;
window.cycleSpeakerTag = cycleSpeakerTag;
window.deleteBubble = deleteBubble;
window.addBubbleToPanel = addBubbleToPanel;
window.regenPanelImage = regenPanelImage;

// ============================================================
// NARRAI PRO — STORYBOARD DIRECTOR, READING FLOW & PANELING COMPOSITOR
// ============================================================

window.currentReadingFlow = 'webtoon'; // 'webtoon' (LTR) or 'manga' (RTL)

function setReadingFlow(flow) {
    window.currentReadingFlow = flow;
    const pages = document.querySelectorAll('.pro-comic-page');
    pages.forEach(p => {
        p.classList.remove('flow-manga', 'flow-webtoon');
        p.classList.add(flow === 'manga' ? 'flow-manga' : 'flow-webtoon');
    });

    // Update active button state in Storyboard Deck
    document.querySelectorAll('.sb-flow-btn').forEach(b => {
        if (b.dataset.flow === flow) {
            b.classList.add('active');
        } else {
            b.classList.remove('active');
        }
    });

    // Update flow indicator labels
    document.querySelectorAll('.reading-flow-indicator').forEach(ind => {
        if (flow === 'manga') {
            ind.innerHTML = '<span class="flow-direction-icon">◂</span> DÒNG ĐỌC: PHẢI ➔ TRÁI (MANGA CHUẨN)';
        } else {
            ind.innerHTML = '<span class="flow-direction-icon">▸</span> DÒNG ĐỌC: TRÁI ➔ PHẢI (WEBTOON HIỆN ĐẠI)';
        }
    });
}
window.setReadingFlow = setReadingFlow;

const STORYBOARD_ACT_DEFS = [
    {
        actNumber: 'I',
        name: 'KHỞI TẠO BỐI CẢNH & GẶP GỠ',
        enName: 'ESTABLISHING & SETUP',
        badgeColor: '#0284c7',
        tagline: 'Mở đầu câu chuyện, giới thiệu thế giới và tạo lập xung đột ban đầu.'
    },
    {
        actNumber: 'II',
        name: 'DIỄN BIẾN, XUNG ĐỘT & ĐỐI ĐẦU',
        enName: 'RISING ACTION & CONFLICT',
        badgeColor: '#F59E0B',
        tagline: 'Mâu thuẫn bùng nổ, hành động dồn dập, đối thoại kịch tính và thử thách sinh tử.'
    },
    {
        actNumber: 'III',
        name: 'CAO TRÀO & BƯỚC NGOẶT ĐỊNH MỆNH',
        enName: 'CLIMAX & RESOLUTION',
        badgeColor: '#dc2626',
        tagline: 'Đòn quyết định phân định thắng bại, bí mật hé lộ và mở ra hành trình tiếp nối.'
    }
];

function groupPanelsIntoStoryboardActs(panels) {
    if (!Array.isArray(panels) || panels.length === 0) return [];

    // Check if panels already have distinct scene_id (S01, S02, S03)
    const sceneIds = [...new Set(panels.map(p => p.scene_id).filter(Boolean))];
    if (sceneIds.length > 1) {
        const acts = [];
        sceneIds.forEach((scId, idx) => {
            const actPanels = panels.filter(p => p.scene_id === scId);
            const def = STORYBOARD_ACT_DEFS[idx % STORYBOARD_ACT_DEFS.length];
            acts.push({
                ...def,
                sceneId: scId,
                location: actPanels[0]?.location || '',
                panels: actPanels
            });
        });
        return acts;
    }

    // Default 3-Act Storyboard Split
    const total = panels.length;
    const countPerAct = Math.max(2, Math.ceil(total / 3));
    const acts = [];

    for (let a = 0; a < 3; a++) {
        const start = a * countPerAct;
        const slice = panels.slice(start, start + countPerAct);
        if (slice.length > 0) {
            const def = STORYBOARD_ACT_DEFS[a];
            acts.push({
                ...def,
                sceneId: `S0${a + 1}`,
                location: slice[0]?.location || '',
                panels: slice
            });
        }
    }
    return acts;
}

function renderStoryboardDirectorDeck(totalPanels, actsCount, container) {
    const deck = document.createElement('div');
    deck.className = 'storyboard-director-deck';

    deck.innerHTML = `
        <div class="sb-info-group">
            <span class="sb-badge-main">🎬 STORYBOARD DIRECTOR</span>
            <div class="sb-title-wrap">
                <div class="sb-title">
                    <span>Bảng Phân Cảnh & Paneling Truyện Tranh</span>
                    <span style="color:#38bdf8; font-size:0.85rem; font-weight:700;">[${actsCount} Hồi • ${totalPanels} Khung Tranh]</span>
                </div>
                <div class="sb-subtitle">Bố cục Paneling động theo kịch bản chuẩn • Bong bóng thoại hình oval đứng Manga</div>
            </div>
        </div>
        <div class="sb-flow-controls">
            <span class="sb-flow-label">Dòng Đọc:</span>
            <button type="button" class="sb-flow-btn ${window.currentReadingFlow === 'webtoon' ? 'active' : ''}" data-flow="webtoon" onclick="setReadingFlow('webtoon')">
                🌐 Webtoon (Trái ➔ Phải)
            </button>
            <button type="button" class="sb-flow-btn ${window.currentReadingFlow === 'manga' ? 'active' : ''}" data-flow="manga" onclick="setReadingFlow('manga')">
                🇯🇵 Manga (Phải ➔ Trái)
            </button>
        </div>
    `;

    container.appendChild(deck);
}

function renderStoryboardAct(act, actIndex, grid) {
    const actSection = document.createElement('section');
    actSection.className = 'storyboard-act-section';
    actSection.id = `storyboard-act-${actIndex + 1}`;

    // 1. Act Header Bar
    const header = document.createElement('div');
    header.className = 'storyboard-act-header';

    const titleBox = document.createElement('div');
    titleBox.className = 'act-title-box';

    const badge = document.createElement('span');
    badge.className = 'act-badge';
    badge.style.background = act.badgeColor || '#F59E0B';
    badge.textContent = `HỒI ${act.actNumber}`;
    titleBox.appendChild(badge);

    const name = document.createElement('h3');
    name.className = 'act-name';
    name.textContent = act.name;
    titleBox.appendChild(name);

    if (act.location) {
        const locTag = document.createElement('span');
        locTag.className = 'act-location-tag';
        locTag.textContent = `📍 ${act.location}`;
        titleBox.appendChild(locTag);
    }

    header.appendChild(titleBox);

    // Reading Flow Indicator
    const flowInd = document.createElement('div');
    flowInd.className = 'reading-flow-indicator';
    const isManga = window.currentReadingFlow === 'manga';
    flowInd.innerHTML = isManga
        ? '<span class="flow-direction-icon">◂</span> DÒNG ĐỌC: PHẢI ➔ TRÁI (MANGA CHUẨN)'
        : '<span class="flow-direction-icon">▸</span> DÒNG ĐỌC: TRÁI ➔ PHẢI (WEBTOON HIỆN ĐẠI)';
    header.appendChild(flowInd);

    actSection.appendChild(header);

    // 2. Paneling Page Grid
    const pageGrid = document.createElement('div');
    const flowClass = window.currentReadingFlow === 'manga' ? 'flow-manga' : 'flow-webtoon';
    pageGrid.className = `pro-comic-page ${flowClass}`;

    act.panels.forEach((p, pIdx) => {
        renderProComicPanel(p, pIdx, pageGrid, act);
    });

    actSection.appendChild(pageGrid);
    grid.appendChild(actSection);
}

// ============================================================
// NARRAI PRO — Main Comic Generation (uses generate-pro)
// ============================================================

async function adaptToComic() {
    let text = document.getElementById('storyOutput')?.innerText?.trim() || "";
    if (!text || text.length < 10) {
        text = document.getElementById('initialPrompt')?.value?.trim() || "";
    }
    if (!text || text.length < 5) {
        text = "Một câu chuyện hành động kịch tính và hào hùng, nhân vật chính bước lên con đường chinh phục đỉnh cao giữa giang hồ hiểm ác.";
    }

    document.getElementById('editorView').style.display = 'none';
    document.getElementById('comicView').style.display = 'block';
    if (typeof BackgroundManager !== 'undefined') BackgroundManager.setContext('comic');

    // Load stability config silently (no UI shown to user)
    if (!stabilityConfigLoaded) {
        loadStabilityConfig();
    }

    const grid = document.getElementById('comicGrid');

    // Cache: if same text + already rendered, keep
    if (hasGeneratedComic && text === lastComicText && grid.children.length > 0) {
        return;
    }

    lastComicText = text;
    hasGeneratedComic = true;

    grid.innerHTML = '';
    const loader = document.getElementById('comicLoading');
    loader.style.display = 'block';
    proResetProgress();

    // Friendly Animated Step Progress
    proAdvanceProgress(0); // Phân tích ý tưởng
    await new Promise(r => setTimeout(r, 500));
    proAdvanceProgress(1); // Xây dựng cốt truyện
    await new Promise(r => setTimeout(r, 500));
    proAdvanceProgress(2); // Thiết kế nhân vật
    await new Promise(r => setTimeout(r, 500));
    proAdvanceProgress(3); // Phân cảnh truyện tranh
    await new Promise(r => setTimeout(r, 500));

    try {
        proAdvanceProgress(4); // Tạo tranh AI

        const res = await fetch(`${API_URL}/comic/generate-pro`, {
            method: 'POST',
            headers: authHeaders(),
            body: JSON.stringify({
                story_id: globalData.storyId || null,
                story_text: text.substring(0, 30000),
                genre: '',
                style: ''
            })
        });

        if (!res.ok) {
            let errMsg = `API lỗi (${res.status})`;
            try { const ed = await res.json(); errMsg = ed.message || ed.detail || errMsg; } catch(_) {}
            throw new Error(errMsg);
        }

        const data = await res.json();
        proAdvanceProgress(5); // Hoàn thiện comic
        await new Promise(r => setTimeout(r, 400));

        loader.style.display = 'none';
        proCompleteProgress();

        if (data.status === 'success') {
            if (!Array.isArray(data.panels) || data.panels.length === 0) {
                throw new Error('Không tạo được khung tranh.');
            }

            // Render using Storyboard Director, Reading Flow & Paneling Engine
            const acts = groupPanelsIntoStoryboardActs(data.panels);
            renderStoryboardDirectorDeck(data.panels.length, acts.length, grid);
            acts.forEach((act, actIdx) => {
                renderStoryboardAct(act, actIdx, grid);
            });

        } else {
            alert('Lỗi tạo truyện tranh: ' + (data.message || data.detail || 'Lỗi hệ thống'));
        }

    } catch(e) {
        loader.style.display = 'none';
        console.warn('[NarrAI Pro] generate-pro failed, trying generate fallback:', e.message);
        try {
            const res2 = await fetch(`${API_URL}/comic/generate`, {
                method: 'POST',
                headers: authHeaders(),
                body: JSON.stringify({
                    story_id: globalData.storyId || null,
                    story_text: text.substring(0, 30000),
                    enhancement_mode: currentEnhancementMode,
                    strength: currentEnhancementStrength
                })
            });
            if (res2.ok) {
                const data2 = await res2.json();
                if (data2.status === 'success' && Array.isArray(data2.panels)) {
                    const acts = groupPanelsIntoStoryboardActs(data2.panels);
                    renderStoryboardDirectorDeck(data2.panels.length, acts.length, grid);
                    acts.forEach((act, actIdx) => {
                        renderStoryboardAct(act, actIdx, grid);
                    });
                    return;
                }
            }
        } catch(e2) { console.warn('Fallback also failed:', e2); }
        alert(`Không thể tạo truyện tranh: ${e.message}`);
    }
}

function backToEditor() {
    document.getElementById('comicView').style.display = 'none';
    document.getElementById('editorView').style.display = 'block';
    if (typeof BackgroundManager !== 'undefined') BackgroundManager.setContext('editor');
}

// ============================================================
// NARRAI — AI Studio Chatbot Background Controller
// ============================================================
const AIStudioChat = {
    panel: null,
    artLayer: null,
    holoLayer: null,

    init() {
        this.panel = document.getElementById('aiCopilotPanel');
        this.artLayer = document.getElementById('aiStudioArtLayer');
        this.holoLayer = document.getElementById('aiStudioHolograms');
        if (!this.panel) return;

        // Input typing listeners
        const inputs = [
            document.getElementById('chatInputText'),
            document.getElementById('chatInput'),
            document.getElementById('aiCustomInstruction')
        ];

        inputs.forEach(inp => {
            if (!inp) return;
            inp.addEventListener('focus', () => this.setState('typing'));
            inp.addEventListener('input', () => this.setState('typing'));
            inp.addEventListener('blur', () => {
                if (this.panel && !this.panel.classList.contains('state-thinking')) {
                    this.setState('idle');
                }
            });
        });

        // Enter key to send message
        const chatInputText = document.getElementById('chatInputText');
        if (chatInputText) {
            chatInputText.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    sendAssistantMessage();
                }
            });
        }

        const chatInput = document.getElementById('chatInput');
        if (chatInput) {
            chatInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    sendChatMessage();
                }
            });
        }

        // Subtle Parallax Effect on Mouse Move
        this.panel.addEventListener('mousemove', (e) => {
            if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
            const rect = this.panel.getBoundingClientRect();
            const x = (e.clientX - rect.left) / rect.width - 0.5;
            const y = (e.clientY - rect.top) / rect.height - 0.5;

            if (this.artLayer) {
                this.artLayer.style.transform = `translate3d(${x * 6}px, ${y * 6}px, 0)`;
            }
            if (this.holoLayer) {
                this.holoLayer.style.transform = `translate3d(${x * -10}px, ${y * -10}px, 0)`;
            }
        });

        this.panel.addEventListener('mouseleave', () => {
            if (this.artLayer) this.artLayer.style.transform = '';
            if (this.holoLayer) this.holoLayer.style.transform = '';
        });
    },

    setState(state) {
        if (!this.panel) return;
        this.panel.classList.remove('state-typing', 'state-thinking');
        if (state === 'typing') {
            this.panel.classList.add('state-typing');
        } else if (state === 'thinking') {
            this.panel.classList.add('state-thinking');
        }
    }
};

// =================== INTERACTIVE CHAT UI ===================
async function sendAssistantMessage() {
    const input = document.getElementById('chatInputText');
    if (!input) return;
    const msg = input.value.trim();
    if (!msg) return;
    
    // Add User Message
    addMessageToChat('user', msg);
    input.value = '';
    
    // Show AI Loading & Activate Thinking Background
    const loader = document.getElementById('aiLoading');
    if (loader) loader.style.display = 'block';
    if (typeof AIStudioChat !== 'undefined') AIStudioChat.setState('thinking');
    
    try {
        const storyContext = document.getElementById('storyOutput')?.innerText?.slice(-6000) || '';
        const res = await fetch(`${API_URL}/copilot-event`, {
            method: 'POST',
            headers: authHeaders(),
            body: JSON.stringify({ 
                session_id: globalData.sessionId || 'temp',
                story_id: globalData.storyId || null,
                event_type: 'USER_CHAT', 
                event_data: JSON.stringify({
                    user_message: msg,
                    current_story: storyContext
                })
            })
        });
        
        const data = await res.json();
        if (loader) loader.style.display = 'none';
        if (typeof AIStudioChat !== 'undefined') AIStudioChat.setState('idle');
        
        if (!res.ok || data.status !== 'success') {
            addMessageToChat('ai', data.message || data.detail || 'Không thể xử lý yêu cầu lúc này.');
        } else {
            const action = data.data?.action || 'reply_user';
            const params = data.data?.action_params || {};

            if (action === 'reply_user') {
                addMessageToChat('ai', params.message || 'Tôi đã nhận được tin nhắn của bạn.');
            } else if (action === 'command_writer') {
                if (params.message) addMessageToChat('ai', params.message);
                await continueWritingWithInstruction(params.instruction);
            } else if (action === 'reject_and_rewrite') {
                addMessageToChat('ai', 'Trợ lý: Đang yêu cầu viết lại vì bản nháp không đạt yêu cầu: ' + (params.critique || ''));
                await continueWritingWithInstruction(params.fix_instruction || params.instruction || params.critique);
            } else {
                addMessageToChat('ai', params.message || ('Đã xử lý xong tác vụ: ' + action));
            }
        }
    } catch (err) {
        if (loader) loader.style.display = 'none';
        if (typeof AIStudioChat !== 'undefined') AIStudioChat.setState('idle');
        addMessageToChat('ai', 'Lỗi kết nối máy chủ Copilot. Vui lòng thử lại.');
    }
}

function formatMessageText(text) {
    if (!text) return '';
    let t = String(text);
    // If text starts with JSON wrapper, unpack message
    if (t.trim().startsWith('{') && t.includes('"message"')) {
        try {
            const p = JSON.parse(t.trim());
            if (p.action_params?.message) t = p.action_params.message;
            else if (p.message) t = p.message;
        } catch (_) {
            const m = t.match(/"message"\s*:\s*"([\s\S]*?)"(?:\s*,\s*"|\s*\}\s*\})/);
            if (m) t = m[1];
        }
    }
    // Escape HTML then render basic markdown
    t = t.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    t = t.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    t = t.replace(/\*(.*?)\*/g, '<em>$1</em>');
    t = t.replace(/`([^`]+)`/g, '<code style="background:rgba(56,189,248,0.15);padding:1px 4px;border-radius:3px;color:#38bdf8;">$1</code>');
    t = t.replace(/\n/g, '<br>');
    return t;
}

function addMessageToChat(role, text) {
    const history = document.getElementById('chatHistory');
    if (!history) return;
    const msgDiv = document.createElement('div');
    msgDiv.className = role === 'user' ? 'chat-message chat-user' : 'chat-message chat-ai';
    msgDiv.innerHTML = formatMessageText(text);
    history.appendChild(msgDiv);
    history.scrollTop = history.scrollHeight;
}


// =================== STORY ACTION BUTTONS ===================

async function continueWriting(userInstruction = '') {
    const storyOutput = document.getElementById('storyOutput');
    const chatHistory = document.getElementById('chatHistory');

    if (!storyOutput.innerText || storyOutput.innerText.length < 10) {
        alert('Chua co noi dung truyen de viet tiep!');
        return;
    }

    chatHistory.innerHTML += '<div class="chat-message chat-user">Viet tiep chuong moi</div>';
    chatHistory.innerHTML += '<div class="chat-message chat-ai" style="color:#d97706">AI dang viet chuong moi...</div>';
    chatHistory.scrollTop = chatHistory.scrollHeight;

    if (typeof AIStudioChat !== 'undefined') AIStudioChat.setState('thinking');

    // Use memory-based endpoint if session exists, fallback to /api/chat
    if (globalData.sessionId) {
        try {
            const response = await fetch(`${API_URL}/generate-chapter`, {
                method: 'POST',
                headers: authHeaders(),
                body: JSON.stringify({
                    session_id: globalData.sessionId,
                    user_instruction: userInstruction
                })
            });

            if (!response.ok) throw new Error('Server error');

            const reader = response.body.getReader();
            const decoder = new TextDecoder('utf-8');
            let newChapter = '';
            
            // Luu lai noi dung cu truoc khi stream chuong moi
            const originalHTML = storyOutput.innerHTML;
            // Them mot the div tam thoi de chua noi dung stream
            const streamContainerId = 'stream-' + Date.now();
            storyOutput.innerHTML = originalHTML + `<div id="${streamContainerId}"></div>`;

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                const chunk = decoder.decode(value, { stream: true });
                stopLatencySensor();
                newChapter += chunk;
                
                // Live update
                const formatted = cleanStreamText(newChapter).split('\n').filter(l => l.trim()).map(l => `<p>${l}</p>`).join('');
                const container = document.getElementById(streamContainerId);
                if (container) {
                    container.innerHTML = formatted;
                }
                updateWordCount();
            }

            const generationError = getStreamError(newChapter);
            if (generationError) {
                const streamContainer = document.getElementById(streamContainerId);
                if (streamContainer) streamContainer.remove();
                const loadingMessage = chatHistory.querySelectorAll('.chat-message');
                if (loadingMessage.length > 0) loadingMessage[loadingMessage.length - 1].remove();
                const errorMessage = document.createElement('div');
                errorMessage.className = 'chat-message chat-ai';
                errorMessage.style.color = 'red';
                errorMessage.textContent = generationError;
                chatHistory.appendChild(errorMessage);
                if (typeof AIStudioChat !== 'undefined') AIStudioChat.setState('idle');
                return;
            }
            
            // Xoa the div tam thoi va gop noi dung vao chinh
            const container = document.getElementById(streamContainerId);
            if (container) {
                const finalContent = container.innerHTML;
                storyOutput.innerHTML = originalHTML + '<br><br>' + finalContent;
            }

            // Remove loading message in chat
            const msgs = chatHistory.querySelectorAll('.chat-message');
            if (msgs.length > 0) msgs[msgs.length - 1].remove();
            chatHistory.innerHTML += '<div class="chat-message chat-ai">Da viet xong chuong moi! Ban co the tiep tuc ra lenh hoac chinh sua truc tiep.</div>';
            
            // Update words count
            updateWordCount();

        } catch (err) {
            chatHistory.innerHTML += '<div class="chat-message chat-ai" style="color:red">Lỗi kết nối. Vui lòng thử lại!</div>';
        } finally {
            if (typeof AIStudioChat !== 'undefined') AIStudioChat.setState('idle');
        }
    } else {
        // Fallback: use legacy /api/chat
        try {
            const res = await fetch(`${API_URL}/chat`, {
                method: 'POST',
                headers: authHeaders(),
                body: JSON.stringify({
                    story_text: storyOutput.innerText,
                    story_id: globalData.storyId,
                    user_message: userInstruction || 'Hay viet tiep chuong tiep theo. Toi thieu 2000 tu. Ket thuc bang Cliffhanger.'
                })
            });
            const data = await res.json();
            const msgs = chatHistory.querySelectorAll('.chat-message');
            if (msgs.length > 0) msgs[msgs.length - 1].remove();
            chatHistory.innerHTML += `<div class="chat-message chat-ai">${data.chat_reply || 'Da viet xong!'}</div>`;
            if (data.new_story_content) {
                storyOutput.innerHTML += '<br><br>' + data.new_story_content.replace(/\n/g, '<br>');
            }
            updateWordCount();
        } catch (err) {
            chatHistory.innerHTML += '<div class="chat-message chat-ai" style="color:red">Lỗi kết nối.</div>';
        } finally {
            if (typeof AIStudioChat !== 'undefined') AIStudioChat.setState('idle');
        }
    }
}

async function continueWritingWithInstruction(instruction) {
    await continueWriting(instruction || 'Hay dieu chinh va viet tiep theo yeu cau cua tac gia.');
}

async function endStory() {
    const storyOutput = document.getElementById('storyOutput');
    const chatHistory = document.getElementById('chatHistory');

    if (!storyOutput.innerText || storyOutput.innerText.length < 10) {
        alert('Chua co noi dung truyen de ket thuc!');
        return;
    }

    if (!confirm('Ban co chac muon ket thuc cau truyen? AI se viet doan ket cho ban.')) return;

    chatHistory.innerHTML += '<div class="chat-message chat-user">Ket thuc cau truyen</div>';
    chatHistory.innerHTML += '<div class="chat-message chat-ai" style="color:#d97706">AI dang viet doan ket...</div>';
    chatHistory.scrollTop = chatHistory.scrollHeight;

    if (globalData.sessionId) {
        try {
            const response = await fetch(`${API_URL}/end-story`, {
                method: 'POST',
                headers: authHeaders(),
                body: JSON.stringify({ session_id: globalData.sessionId })
            });

            if (!response.ok) throw new Error('Server error');

            const reader = response.body.getReader();
            const decoder = new TextDecoder('utf-8');
            let ending = '';
            const originalHTML = storyOutput.innerHTML;
            const streamContainerId = 'stream-end-' + Date.now();
            storyOutput.innerHTML = originalHTML + `<div id="${streamContainerId}"></div>`;

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                const chunk = decoder.decode(value, { stream: true });
            stopLatencySensor();
                ending += chunk;
                
                const formatted = cleanStreamText(ending).split('\n').filter(l => l.trim()).map(l => `<p>${l}</p>`).join('');
                const container = document.getElementById(streamContainerId);
                if (container) {
                    container.innerHTML = formatted;
                }
                updateWordCount();
            }

            const generationError = getStreamError(ending);
            if (generationError) {
                const streamContainer = document.getElementById(streamContainerId);
                if (streamContainer) streamContainer.remove();
                const loadingMessage = chatHistory.querySelectorAll('.chat-message');
                if (loadingMessage.length > 0) loadingMessage[loadingMessage.length - 1].remove();
                const errorMessage = document.createElement('div');
                errorMessage.className = 'chat-message chat-ai';
                errorMessage.style.color = 'red';
                errorMessage.textContent = generationError;
                chatHistory.appendChild(errorMessage);
                return;
            }
            
            const container = document.getElementById(streamContainerId);
            if (container) {
                const finalContent = container.innerHTML;
                storyOutput.innerHTML = originalHTML + '<br><br>' + finalContent;
            }

            const msgs = chatHistory.querySelectorAll('.chat-message');
            if (msgs.length > 0) msgs[msgs.length - 1].remove();
            chatHistory.innerHTML += '<div class="chat-message chat-ai">Cau truyen da ket thuc! Ban co the tai xuong hoac chinh sua them.</div>';
            globalData.sessionId = null;

        } catch (err) {
            chatHistory.innerHTML += '<div class="chat-message chat-ai" style="color:red">Lỗi kết nối.</div>';
        }
    } else {
        // Fallback
        try {
            const res = await fetch(`${API_URL}/chat`, {
                method: 'POST',
                headers: authHeaders(),
                body: JSON.stringify({
                    story_text: storyOutput.innerText,
                    user_message: 'Hay viet DOAN KET THUC. Goi gon tat ca tuyen truyen, giai quyet xung dot chinh. Toi thieu 2000 tu.'
                })
            });
            const data = await res.json();
            const msgs = chatHistory.querySelectorAll('.chat-message');
            if (msgs.length > 0) msgs[msgs.length - 1].remove();
            chatHistory.innerHTML += `<div class="chat-message chat-ai">${data.chat_reply || 'Da viet xong!'}</div>`;
            if (data.new_story_content) {
                storyOutput.innerHTML += '<br><br>' + data.new_story_content.replace(/\n/g, '<br>');
            }
            updateWordCount();
        } catch (err) {
            chatHistory.innerHTML += '<div class="chat-message chat-ai" style="color:red">Lỗi kết nối.</div>';
        }
    }
}

// Initialize AI Studio Chatbot Background Controller
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        if (typeof AIStudioChat !== 'undefined') AIStudioChat.init();
    });
} else {
    if (typeof AIStudioChat !== 'undefined') AIStudioChat.init();
}

