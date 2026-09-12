const API_URL = "/api";

let globalData = {
    initialPrompt: "",
    chatHistory: [],
    refinedPrompt: "",
    selectedLength: "medium"
};

// =================== i18n (ĐA NGÔN NGỮ) ===================
const i18nDict = {
    vi: {
        not_logged_in: "Chưa đăng nhập",
        login: "Đăng nhập",
        logout: "Đăng xuất",
        new_story: "➕ Viết truyện mới",
        story_history: "📚 Lịch sử truyện",
        step1_title: "Bước 1: Khởi nguồn ý tưởng",
        genres_label: "🎨 Thể loại truyện (Chọn nhiều):",
        themes_label: "🔥 Chủ đề thịnh hành (Mix nhiều chủ đề):",
        prompt_placeholder: "Ví dụ: Một thế giới nơi phép thuật bị cấm đoán...",
        continue_btn: "Tiếp tục ➔",
        step2_title: "Bước 2: Phỏng vấn Cốt truyện với AI",
        chat_placeholder: "Nhập câu trả lời của bạn... (Bấm Enter để gửi)",
        send_btn: "Gửi",
        skip_chat_btn: "Bỏ qua hỏi đáp, Chốt dàn ý luôn",
        step3_title: "Bước 3: Chốt cấu hình & Viết truyện",
        len_short: "Truyện ngắn (500-800 từ)",
        len_medium: "Tiểu thuyết vừa (1500-2500 từ)",
        len_long: "Dài kỳ (3000-5000 từ)",
        start_writing_btn: "Bắt đầu Chấp bút ✍️",
        editor_title: "Bản Thảo Đang Viết...",
        words: "từ",
        download_btn: "📥 Tải EPUB/PDF",
        editor_placeholder: "Câu chuyện sẽ xuất hiện ở đây. Bạn có thể tự gõ thêm bất cứ lúc nào...",
        tool_rewrite: "✨ Viết lại",
        tool_expand: "🔍 Mở rộng",
        tool_shorten: "✂️ Rút gọn",
        tool_ai: "🤖 Tùy chỉnh với AI",
        ai_copilot: "🤖 AI Co-pilot",
        ai_welcome_1: "Chào mừng bạn đến với không gian làm việc chuyên nghiệp.",
        tip: "💡 <b>Mẹo:</b>",
        ai_welcome_2: "Trong quá trình viết, hãy bôi đen một đoạn văn chưa ưng ý trong Bản thảo. AI sẽ giúp bạn sửa lại nó ngay lập tức!",
        selected_text: "Đoạn văn đang chọn:",
        ai_instruction_placeholder: "Ví dụ: Đổi giọng văn buồn bã hơn...",
        ai_request_btn: "Yêu cầu AI sửa 🚀",
        ai_result: "Kết quả từ AI:",
        accept_btn: "✅ Thay thế",
        reject_btn: "❌ Hủy bỏ",
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
        new_story: "➕ New Story",
        story_history: "📚 Story History",
        step1_title: "Step 1: Idea Generation",
        genres_label: "🎨 Genres (Multi-select):",
        themes_label: "🔥 Trending Themes (Mix):",
        prompt_placeholder: "Example: A world where magic is forbidden...",
        continue_btn: "Continue ➔",
        step2_title: "Step 2: Plot Interview with AI",
        chat_placeholder: "Type your answer... (Press Enter to send)",
        send_btn: "Send",
        skip_chat_btn: "Skip Q&A, Finalize Outline",
        step3_title: "Step 3: Configuration & Generation",
        len_short: "Short (500-800 words)",
        len_medium: "Medium (1500-2500 words)",
        len_long: "Long (3000-5000 words)",
        start_writing_btn: "Start Writing ✍️",
        editor_title: "Draft in Progress...",
        words: "words",
        download_btn: "📥 Download EPUB/PDF",
        editor_placeholder: "Your story will appear here. You can type freely at any time...",
        tool_rewrite: "✨ Rewrite",
        tool_expand: "🔍 Expand",
        tool_shorten: "✂️ Shorten",
        tool_ai: "🤖 Customize with AI",
        ai_copilot: "🤖 AI Co-pilot",
        ai_welcome_1: "Welcome to your professional workspace.",
        tip: "💡 <b>Tip:</b>",
        ai_welcome_2: "Highlight a paragraph in your draft that you want to change. AI will help you revise it instantly!",
        selected_text: "Selected text:",
        ai_instruction_placeholder: "Example: Make the tone more melancholy...",
        ai_request_btn: "Ask AI to Revise 🚀",
        ai_result: "AI Result:",
        accept_btn: "✅ Replace",
        reject_btn: "❌ Cancel",
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
    const token = localStorage.getItem('narrai_token');
    if (token) {
        try {
            const res = await fetch(`${API_URL}/me`, { headers: authHeaders() });
            if (res.ok) {
                const data = await res.json();
                document.getElementById('welcomeUser').textContent = currentLang === 'vi' ? `Chào, ${data.username}` : `Hi, ${data.username}`;
                document.getElementById('loginBtnSidebar').style.display = 'none';
                document.getElementById('logoutBtnSidebar').style.display = 'block';
                
                // Show App, Hide Landing
                document.getElementById('landingContainer').style.display = 'none';
                document.getElementById('appContainer').style.display = 'flex';
                return;
            } else {
                logout(); // invalid token
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
}

function logout() {
    localStorage.removeItem('narrai_token');
    checkAuth();
}

function openAuthModal() {
    document.getElementById('authModal').style.display = 'block';
    document.getElementById('authError').textContent = '';
}

function closeAuthModal() {
    document.getElementById('authModal').style.display = 'none';
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
                closeAuthModal();
                checkAuth();
            } else {
                err.textContent = data.detail || "Đăng nhập thất bại";
            }
        } else {
            const res = await fetch(`${API_URL}/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({username: u, password: p})
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
            chatBox.scrollTop = chatBox.scrollHeight;
            
            if (data.is_ready) forceRefinePrompt();
        }
    } catch (error) {
        document.getElementById('chatLoading').textContent = "Lỗi kết nối.";
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
    
    document.getElementById('setupView').style.display = 'none';
    document.getElementById('editorView').style.display = 'block';
    
    const output = document.getElementById('storyOutput');
    output.innerHTML = `<i>${currentLang==='vi'?'Đang khởi tạo bản thảo...':'Generating draft...'}</i><br><br>`;
    
    try {
        const response = await fetch(`${API_URL}/generate-story`, {
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
            fullStory += chunk;
            
            const formattedStory = fullStory
                .split('\n')
                .filter(line => line.trim())
                .map(line => `<p>${line}</p>`)
                .join('');
            
            output.innerHTML = formattedStory;
            updateWordCount();
        }
    } catch (error) {
        output.innerHTML += `<p style="color: red;">Lỗi: ${error.message}</p>`;
    }
}

function updateWordCount() {
    const text = document.getElementById('storyOutput').innerText;
    const count = text.trim().split(/\s+/).filter(w => w.length > 0).length;
    const label = i18nDict[currentLang]['words'];
    document.getElementById('wordCount').textContent = `${count} ${label}`;
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
    { vi: "Ngôn tình", en: "Romance" }, { vi: "Đam mỹ", en: "Boys' Love (BL)" }, { vi: "Bách hợp", en: "Girls' Love (GL)" }, { vi: "Thanh xuân", en: "School Life" }, { vi: "Cưới trước yêu sau", en: "Arranged Marriage" },
    // Nhóm 2: Kỳ ảo
    { vi: "Tiên hiệp", en: "Xianxia" }, { vi: "Kiếm hiệp", en: "Wuxia" }, { vi: "Huyền huyễn", en: "Xuanhuan" }, { vi: "Kỳ ảo", en: "Fantasy" }, { vi: "Khoa học viễn tưởng", en: "Sci-Fi" }, { vi: "Xuyên không", en: "Isekai" }, { vi: "Trọng sinh", en: "Rebirth" }, { vi: "Hệ thống", en: "System" }, { vi: "Mạt thế", en: "Post-Apocalyptic" },
    // Nhóm 3: Hành động
    { vi: "Hành động", en: "Action" }, { vi: "Phiêu lưu", en: "Adventure" }, { vi: "Võng du", en: "LitRPG" },
    // Nhóm 4: Bí ẩn
    { vi: "Trinh thám", en: "Mystery" }, { vi: "Kinh dị", en: "Horror" }, { vi: "Giật gân", en: "Thriller" }, { vi: "Linh dị", en: "Supernatural" },
    // Nhóm 5: Đời sống
    { vi: "Đô thị", en: "Urban" }, { vi: "Điền văn", en: "Slice of Life" }, { vi: "Hài hước", en: "Comedy" }, { vi: "Bi kịch", en: "Tragedy" }, { vi: "Lịch sử", en: "Historical" }, { vi: "Cung đấu", en: "Palace Scheme" }
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
        
        const tag = document.createElement('div');
        tag.className = 'trending-tag';
        if (selectedTags.has(genre.vi)) {
            tag.classList.add('selected-tag');
        }
        tag.textContent = textToDisplay;
        tag.onclick = (e) => {
            e.preventDefault();
            tag.classList.toggle('selected-tag');
            if (selectedTags.has(genre.vi)) selectedTags.delete(genre.vi);
            else selectedTags.add(genre.vi);
        };
        genresContainer.appendChild(tag);
    });
}

function filterGenres() {
    const searchVal = document.getElementById('genreSearch').value;
    initGenres(searchVal);
}

async function fetchTrendingTopics() {
    try {
        // Fallback mock data in case API fails
        const mockData = [
            { title: { vi: "Anh hùng chuyển sinh", en: "Reborn Hero" } },
            { title: { vi: "Thế giới ngầm", en: "Underworld" } },
            { title: { vi: "Tình yêu cấm đoán", en: "Forbidden Love" } }
        ];
        
        const trendingContainer = document.getElementById('trendingContainer');
        if (!trendingContainer) return;
        trendingContainer.innerHTML = '';
        
        // Use mock data for immediate UI response (as the json might not be bilingual natively)
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
    initGenres();
    setLang(currentLang);
    checkAuth();
    
    // Add Enter key listeners
    const chatInput = document.getElementById('chatInput');
    if (chatInput) {
        chatInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendChatMessage(); }
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
                <div class="history-meta">🕒 ${s.created_at} | 📝 ${s.word_count} ${i18nDict[currentLang]['words']}</div>
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
    const list = document.getElementById('historyList');
    list.innerHTML = i18nDict[currentLang]['loading'];
    
    // Apply SWR
    fetchWithSWR('cache_stories', `${API_URL}/stories`, { headers: authHeaders() }, renderHistoryList);
}

function closeHistory() { document.getElementById('historyModal').style.display = 'none'; }
window.onclick = function(event) { 
    if (event.target == document.getElementById('historyModal')) closeHistory(); 
    if (event.target == document.getElementById('authModal')) closeAuthModal(); 
}

function renderStoryDetail(data) {
    const output = document.getElementById('storyOutput');
    if(data.status === 'success') {
        const formattedStory = data.story.story_content
            .split('\n')
            .filter(line => line.trim())
            .map(line => `<p>${line}</p>`)
            .join('');
        output.innerHTML = formattedStory;
        updateWordCount();
    } else {
        output.innerHTML = `<p style="color:red;">${data.message}</p>`;
    }
}

async function loadStory(id) {
    closeHistory();
    document.getElementById('setupView').style.display = 'none';
    document.getElementById('editorView').style.display = 'block';
    
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

// =================== COMIC GENERATION ===================
let lastComicText = "";
let hasGeneratedComic = false;

async function adaptToComic() {
    const text = document.getElementById('storyOutput').innerText;
    if (!text || text.length < 10) {
        alert('Cần gõ ít nhất 10 kí tự vào trang giấy để AI có nội dung chuyển thể truyện tranh!');
        return;
    }
    
    document.getElementById('editorView').style.display = 'none';
    document.getElementById('comicView').style.display = 'block';
    
    // Nếu nội dung không đổi và đã từng tạo ảnh -> dùng lại lưới ảnh cũ
    if (hasGeneratedComic && text === lastComicText) {
        return; // Bỏ qua việc gọi API lại
    }
    
    // Cập nhật trạng thái
    lastComicText = text;
    hasGeneratedComic = true;
    
    const grid = document.getElementById('comicGrid');
    grid.innerHTML = '';
    const loader = document.getElementById('comicLoading');
    loader.style.display = 'block';
    
    try {
        const res = await fetch(`${API_URL}/comic/generate`, {
            method: 'POST',
            headers: authHeaders(),
            body: JSON.stringify({ story_id: 1, story_text: text.substring(0, 30000) })
        });
        const data = await res.json();
        loader.style.display = 'none';
        
        if (data.status === 'success') {
            data.panels.forEach((p, index) => {
                const panelDiv = document.createElement('div');
                panelDiv.className = `comic-panel panel-${p.layout_type}`;
                
                const img = document.createElement('img');
                img.alt = p.image_prompt || 'Comic Panel';
                panelDiv.appendChild(img);
                
                // Stagger image loading by 1 second each to prevent Pollinations API from rate limiting (429 Too Many Requests)
                setTimeout(() => {
                    img.src = p.image_url;
                }, index * 1000);
                
                if (p.dialogue_text) {
                    const bubble = document.createElement('div');
                    bubble.className = 'speech-bubble';
                    bubble.innerText = p.dialogue_text;
                    panelDiv.appendChild(bubble);
                }
                
                grid.appendChild(panelDiv);
            });
        } else {
            alert('Lỗi tạo truyện tranh: ' + (data.message || data.detail || 'Lỗi hệ thống'));
            backToEditor();
        }
    } catch(e) {
        loader.style.display = 'none';
        alert('Lỗi kết nối hoặc Backend chưa cập nhật xong!');
        backToEditor();
    }
}

function backToEditor() {
    document.getElementById('comicView').style.display = 'none';
    document.getElementById('editorView').style.display = 'block';
}

// =================== INTERACTIVE CHAT UI ===================
async function sendChatMessage() {
    const input = document.getElementById('chatInputText');
    const msg = input.value.trim();
    if (!msg) return;
    
    // Add User Message
    addMessageToChat('user', msg);
    input.value = '';
    
    // Get current story state
    const currentStory = document.getElementById('storyOutput').innerText;
    
    // Show AI Loading
    const loader = document.getElementById('aiLoading');
    loader.style.display = 'block';
    
    try {
        const res = await fetch(`${API_URL}/chat`, {
            method: 'POST',
            headers: authHeaders(),
            body: JSON.stringify({ 
                story_text: currentStory, 
                user_message: msg 
            })
        });
        
        const data = await res.json();
        loader.style.display = 'none';
        
        if (res.status === 401) { alert('Vui lòng đăng nhập lại.'); return; }
        
        if (data.status === 'success') {
            // Add AI response to chat
            addMessageToChat('ai', data.chat_reply);
            
            // Append new story content if provided
            if (data.new_story_content) {
                const editor = document.getElementById('storyOutput');
                if (editor.innerText.trim() !== '') {
                    editor.innerHTML += '<br><br>';
                }
                // Format the text and append
                const formatted = data.new_story_content.replace(/\*\*(.*?)\*\*/g, '<b>$1</b>').replace(/\n/g, '<br>');
                editor.innerHTML += formatted;
                
                // Update word count
                const wordCount = editor.innerText.trim().split(/\s+/).filter(w => w.length > 0).length;
                document.getElementById('wordCount').innerHTML = `${wordCount} <span data-i18n="words">từ</span>`;
                
                // Scroll to bottom
                editor.scrollTop = editor.scrollHeight;
            }
        } else {
            addMessageToChat('ai', 'Lỗi: ' + (data.detail || 'Không thể kết nối.'));
        }
    } catch (err) {
        loader.style.display = 'none';
        addMessageToChat('ai', 'L?i m?ng ho?c m�y ch? kh�ng ph?n h?i.');
    }
}

function addMessageToChat(role, text) {
    const history = document.getElementById('chatHistory');
    const msgDiv = document.createElement('div');
    msgDiv.className = \chat-msg \\;
    msgDiv.innerText = text;
    history.appendChild(msgDiv);
    history.scrollTop = history.scrollHeight;
}
