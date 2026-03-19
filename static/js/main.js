/**
 * Daily arXiv - Modern Frontend JavaScript
 */

const LANG = window.APP_LANGUAGE === 'en' ? 'en' : 'zh';
const I18N = {
    zh: {
        monthNames: ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月'],
        weekDays: ['日', '一', '二', '三', '四', '五', '六'],
        loading: '加载中...',
        loadingPapers: '加载论文中...',
        loadAnalysisFailed: '加载分析失败',
        noWordcloud: '暂无词云数据',
        wordcloudLoadFailed: '词云加载失败',
        noPaperData: '暂无论文数据',
        unknown: 'Unknown',
        authorLabel: '作者',
        noAbstract: '暂无摘要',
        viewPdf: '查看PDF',
        viewDetail: '查看详情',
        noPapers: '暂无论文',
        noCategories: '暂无类别',
        allCategories: '全部类别',
        noData: '暂无数据'
    },
    en: {
        monthNames: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
        weekDays: ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],
        loading: 'Loading...',
        loadingPapers: 'Loading papers...',
        loadAnalysisFailed: 'Failed to load analysis',
        noWordcloud: 'No word cloud data',
        wordcloudLoadFailed: 'Failed to load word cloud',
        noPaperData: 'No paper data',
        unknown: 'Unknown',
        authorLabel: 'Authors',
        noAbstract: 'No abstract',
        viewPdf: 'View PDF',
        viewDetail: 'View details',
        noPapers: 'No papers available',
        noCategories: 'No categories',
        allCategories: 'All categories',
        noData: 'No data'
    }
};

function t(key) {
    return I18N[LANG][key] || key;
}

// ===================  全局状态 ==================== //
const state = {
    currentSection: 'overview',
    currentPage: 1,
    papersPerPage: 20,
    selectedCategory: '',
    searchQuery: '',
    allPapers: [],
    allCategories: [],
    currentDate: new Date(),
    theme: localStorage.getItem('theme') || 'light'
};

// ==================== 初始化 ==================== //
document.addEventListener('DOMContentLoaded', async function() {
    initTheme();
    initNavigation();
    initCalendar();
    initEventListeners();
    
    // 加载数据
    await loadAllData();
    
    // 初始化UI组件
    initScrollBehavior();
    initMobileMenu();
});

// ==================== 主题切换 ==================== //
function initTheme() {
    const html = document.documentElement;
    html.setAttribute('data-theme', state.theme);
    
    const themeToggle = document.getElementById('theme-toggle');
    const icon = themeToggle.querySelector('i');
    icon.className = state.theme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
}

function toggleTheme() {
    state.theme = state.theme === 'light' ? 'dark' : 'light';
    localStorage.setItem('theme', state.theme);
    initTheme();
}

// ==================== 导航 ==================== //
function initNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    
    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const section = item.dataset.section;
            navigateToSection(section);
        });
    });
    
    // 处理链接点击
    document.querySelectorAll('[data-section]').forEach(link => {
        link.addEventListener('click', (e) => {
            const section = link.dataset.section;
            if (section) {
                e.preventDefault();
                navigateToSection(section);
            }
        });
    });
}

function navigateToSection(sectionName) {
    // 更新状态
    state.currentSection = sectionName;
    
    // 更新导航栏
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.toggle('active', item.dataset.section === sectionName);
    });
    
    // 切换内容区域
    document.querySelectorAll('.content-section').forEach(section => {
        section.classList.toggle('active', section.id === `${sectionName}-section`);
    });
    
    // 关闭移动端菜单
    closeMobileMenu();
    
    // 滚动到顶部
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// ==================== 移动端菜单 ==================== //
function initMobileMenu() {
    const mobileBtn = document.getElementById('mobile-menu-btn');
    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebar-toggle-btn');
    
    if (mobileBtn) {
        mobileBtn.addEventListener('click', toggleMobileMenu);
    }
    
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', closeMobileMenu);
    }
    
    // 点击遮罩关闭
    document.addEventListener('click', (e) => {
        if (sidebar && sidebar.classList.contains('open')) {
            if (!sidebar.contains(e.target) && !mobileBtn.contains(e.target)) {
                closeMobileMenu();
            }
        }
    });
}

function toggleMobileMenu() {
    const sidebar = document.getElementById('sidebar');
    sidebar.classList.toggle('open');
}

function closeMobileMenu() {
    const sidebar = document.getElementById('sidebar');
    sidebar.classList.remove('open');
}

// ==================== 日历 ==================== //
function initCalendar() {
    renderCalendar(state.currentDate);
    
    document.getElementById('prev-month')?.addEventListener('click', () => {
        state.currentDate.setMonth(state.currentDate.getMonth() - 1);
        renderCalendar(state.currentDate);
    });
    
    document.getElementById('next-month')?.addEventListener('click', () => {
        state.currentDate.setMonth(state.currentDate.getMonth() + 1);
        renderCalendar(state.currentDate);
    });
}

function renderCalendar(date) {
    const year = date.getFullYear();
    const month = date.getMonth();
    
    // 更新标题
    const monthNames = I18N[LANG].monthNames;
    document.getElementById('current-month').textContent = LANG === 'en'
        ? `${monthNames[month]} ${year}`
        : `${year}年${monthNames[month]}`;
    
    // 获取月份第一天和最后一天
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const startDay = firstDay.getDay(); // 0 (周日) - 6 (周六)
    const totalDays = lastDay.getDate();
    
    // 生成日历网格
    const calendarBody = document.getElementById('calendar-body');
    calendarBody.innerHTML = '';
    
    // 星期标题
    const weekDays = I18N[LANG].weekDays;
    weekDays.forEach(day => {
        const dayHeader = document.createElement('div');
        dayHeader.className = 'calendar-day-header';
        dayHeader.textContent = day;
        dayHeader.style.cssText = 'font-weight: 600; color: var(--text-secondary); text-align: center; padding: 0.5rem 0;';
        calendarBody.appendChild(dayHeader);
    });
    
    // 填充空白日期
    for (let i = 0; i < startDay; i++) {
        const emptyDay = document.createElement('div');
        emptyDay.className = 'calendar-day empty';
        calendarBody.appendChild(emptyDay);
    }
    
    // 填充日期
    const today = new Date();
    for (let day = 1; day <= totalDays; day++) {
        const dayElement = document.createElement('div');
        dayElement.className = 'calendar-day';
        dayElement.textContent = day;
        
        // 标记今天
        if (year === today.getFullYear() && month === today.getMonth() && day === today.getDate()) {
            dayElement.classList.add('active');
        }
        
        // TODO: 检查是否有数据，添加 has-data 类
        // dayElement.classList.add('has-data');
        
        dayElement.addEventListener('click', () => {
            // TODO: 加载特定日期的数据
            console.log(`Selected date: ${year}-${month + 1}-${day}`);
        });
        
        calendarBody.appendChild(dayElement);
    }
}

// ==================== 数据加载 ==================== //
async function loadAllData() {
    try {
        await Promise.all([
            loadStats(),
            loadAnalysis(),
            loadPapers(),
            loadCategories()
        ]);
    } catch (error) {
        console.error('加载数据失败:', error);
    }
}

async function loadStats() {
    try {
        const response = await fetch('/api/stats');
        if (!response.ok) throw new Error('Failed to load stats');
        
        const stats = await response.json();
        
        // 更新统计卡片
        updateElement('total-papers', stats.papers_count || 0);
        updateElement('total-summaries', stats.summaries_count || 0);
        
        // 更新最后更新时间
        if (stats.last_update) {
            updateElement('last-update-time', stats.last_update);
        }
        
        // 从分析数据获取更多统计
        const analysisRes = await fetch('/api/analysis');
        if (analysisRes.ok) {
            const analysis = await analysisRes.json();
            const keywords = analysis.keywords || [];
            const categories = Object.keys(analysis.statistics?.category_distribution || {});
            
            updateElement('total-categories', categories.length);
            updateElement('hot-topics', Math.min(keywords.length, 10));
        }
    } catch (error) {
        console.error('加载统计数据失败:', error);
    }
}

async function loadAnalysis() {
    try {
        const response = await fetch('/api/analysis');
        if (!response.ok) throw new Error('Failed to load analysis');
        
        const analysis = await response.json();
        
        // 加载词云
        await loadWordcloud();
        
        // 加载LLM分析
        const llmAnalysis = analysis.llm_analysis || {};
        
        renderAnalysisContent('summary-content', llmAnalysis.analysis_summary_html || llmAnalysis.analysis_summary);
        renderAnalysisContent('hotspots-content', llmAnalysis.hotspots_html || llmAnalysis.hotspots);
        renderAnalysisContent('trends-content', llmAnalysis.trends_html || llmAnalysis.trends);
        renderAnalysisContent('future-content', llmAnalysis.future_directions_html || llmAnalysis.future_directions);
        renderAnalysisContent('ideas-content', llmAnalysis.research_ideas_html || llmAnalysis.research_ideas);
        
    } catch (error) {
        console.error('加载分析数据失败:', error);
        showError('hotspots-content', t('loadAnalysisFailed'));
    }
}

async function loadWordcloud() {
    try {
        const response = await fetch('/api/wordcloud');
        if (!response.ok) throw new Error('Failed to load wordcloud');
        
        const data = await response.json();
        const container = document.getElementById('wordcloud-container');
        
        if (data.url) {
            container.innerHTML = `<img src="${data.url}" alt="Wordcloud" class="fade-in">`;
        } else {
            container.innerHTML = `<p style="color: var(--text-secondary);">${t('noWordcloud')}</p>`;
        }
    } catch (error) {
        console.error('加载词云失败:', error);
        const container = document.getElementById('wordcloud-container');
        container.innerHTML = `<p style="color: var(--text-secondary);">${t('wordcloudLoadFailed')}</p>`;
    }
}

async function loadPapers(page = 1) {
    try {
        showLoading('papers-list');
        
        const params = new URLSearchParams({
            page: page,
            per_page: state.papersPerPage,
            category: state.selectedCategory
        });
        
        const response = await fetch(`/api/papers?${params}`);
        if (!response.ok) throw new Error('Failed to load papers');
        
        const data = await response.json();
        state.allPapers = data.papers || [];
        state.currentPage = page;
        
        // 渲染论文列表
        renderPapers(filterPapers(state.allPapers));
        
        // 渲染分页
        renderPagination(data.total_pages, page);
        
        // 渲染热门论文（概览页）
        renderFeaturedPapers(state.allPapers.slice(0, 5));
        
    } catch (error) {
        console.error('加载论文失败:', error);
        showError('papers-list', LANG === 'en' ? 'Failed to load papers' : '加载论文失败');
    }
}

async function loadCategories() {
    try {
        const response = await fetch('/api/categories');
        if (!response.ok) throw new Error('Failed to load categories');
        
        const categories = await response.json();
        state.allCategories = categories;
        
        // 渲染类别列表（侧边栏）
        renderCategoryList(categories);
        
        // 渲染类别筛选（论文列表页）
        renderCategoryFilter(categories);
        
    } catch (error) {
        console.error('加载类别失败:', error);
    }
}

// ==================== 渲染函数 ==================== //
function renderPapers(papers) {
    const container = document.getElementById('papers-list');
    
    if (!papers || papers.length === 0) {
        container.innerHTML = `<p style="text-align: center; color: var(--text-secondary); padding: 3rem;">${t('noPaperData')}</p>`;
        return;
    }
    
    container.innerHTML = papers.map(paper => `
        <div class="paper-card fade-in">
            <div class="paper-header">
                <div>
                    <h3 class="paper-title">
                        <a href="${paper.entry_url}" target="_blank">${escapeHtml(paper.title)}</a>
                    </h3>
                    <div class="paper-meta">
                        <span class="paper-meta-item">
                            <i class="fas fa-calendar"></i>
                            ${paper.published || 'N/A'}
                        </span>
                        <span class="paper-meta-item">
                            <i class="fas fa-user"></i>
                            ${paper.authors ? paper.authors.slice(0, 3).join(', ') : t('unknown')}
                            ${paper.authors && paper.authors.length > 3 ? ' et al.' : ''}
                        </span>
                    </div>
                </div>
            </div>
            <p class="paper-authors">
                <strong>${t('authorLabel')}:</strong> ${paper.authors ? paper.authors.join(', ') : t('unknown')}
            </p>
            <p class="paper-abstract">${escapeHtml(paper.abstract || t('noAbstract'))}</p>
            <div class="paper-categories">
                ${(paper.categories || []).map(cat => 
                    `<span class="category-badge">${escapeHtml(cat)}</span>`
                ).join('')}
            </div>
            <div class="paper-actions">
                <a href="${paper.pdf_url || paper.entry_url}" target="_blank" class="btn-paper btn-primary">
                    <i class="fas fa-file-pdf"></i>
                    ${t('viewPdf')}
                </a>
                <a href="${paper.entry_url}" target="_blank" class="btn-paper btn-secondary">
                    <i class="fas fa-external-link-alt"></i>
                    arXiv
                </a>
            </div>
        </div>
    `).join('');
}

function renderFeaturedPapers(papers) {
    const container = document.getElementById('featured-papers');
    
    if (!papers || papers.length === 0) {
        container.innerHTML = `<p style="text-align: center; color: var(--text-secondary);">${t('noPapers')}</p>`;
        return;
    }
    
    container.innerHTML = papers.map(paper => `
        <div class="paper-card fade-in">
            <h4 class="paper-title">
                <a href="${paper.entry_url}" target="_blank">${escapeHtml(paper.title)}</a>
            </h4>
            <p class="paper-abstract" style="display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;">
                ${escapeHtml(paper.abstract || '')}
            </p>
            <div class="paper-actions" style="margin-top: 0.75rem;">
                <a href="${paper.entry_url}" target="_blank" class="btn-paper btn-primary" style="font-size: 0.875rem; padding: 0.5rem 1rem;">
                    <i class="fas fa-arrow-right"></i>
                    ${t('viewDetail')}
                </a>
            </div>
        </div>
    `).join('');
}

function renderCategoryList(categories) {
    const container = document.getElementById('category-list');
    
    if (!categories || categories.length === 0) {
        container.innerHTML = `<p style="text-align: center; color: var(--text-secondary); font-size: 0.875rem;">${t('noCategories')}</p>`;
        return;
    }
    
    container.innerHTML = categories.slice(0, 10).map(cat => `
        <div class="category-item ${state.selectedCategory === cat.name ? 'active' : ''}" 
             data-category="${escapeHtml(cat.name)}">
            <span class="category-name">${escapeHtml(cat.name)}</span>
            <span class="category-count">${cat.count}</span>
        </div>
    `).join('');
    
    // 绑定点击事件
    container.querySelectorAll('.category-item').forEach(item => {
        item.addEventListener('click', () => {
            const category = item.dataset.category;
            filterByCategory(category === state.selectedCategory ? '' : category);
        });
    });
}

function renderCategoryFilter(categories) {
    const select = document.getElementById('paper-category-filter');
    if (!select) return;
    
    select.innerHTML = `<option value="">${t('allCategories')}</option>` +
        categories.map(cat => 
            `<option value="${escapeHtml(cat.name)}">${escapeHtml(cat.name)} (${cat.count})</option>`
        ).join('');
}

function renderPagination(totalPages, currentPage) {
    const container = document.getElementById('pagination');
    if (!container) return;
    
    const pages = [];
    const maxVisible = 5;
    
    // 上一页
    pages.push(`
        <li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
            <a class="page-link" href="#" data-page="${currentPage - 1}">
                <i class="fas fa-chevron-left"></i>
            </a>
        </li>
    `);
    
    // 页码
    let startPage = Math.max(1, currentPage - Math.floor(maxVisible / 2));
    let endPage = Math.min(totalPages, startPage + maxVisible - 1);
    
    if (endPage - startPage < maxVisible - 1) {
        startPage = Math.max(1, endPage - maxVisible + 1);
    }
    
    for (let i = startPage; i <= endPage; i++) {
        pages.push(`
            <li class="page-item ${i === currentPage ? 'active' : ''}">
                <a class="page-link" href="#" data-page="${i}">${i}</a>
            </li>
        `);
    }
    
    // 下一页
    pages.push(`
        <li class="page-item ${currentPage === totalPages ? 'disabled' : ''}">
            <a class="page-link" href="#" data-page="${currentPage + 1}">
                <i class="fas fa-chevron-right"></i>
            </a>
        </li>
    `);
    
    container.innerHTML = pages.join('');
    
    // 绑定点击事件
    container.querySelectorAll('.page-link').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const page = parseInt(link.dataset.page);
            if (page > 0 && page <= totalPages) {
                loadPapers(page);
                window.scrollTo({ top: 0, behavior: 'smooth' });
            }
        });
    });
}

function renderAnalysisContent(elementId, content) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    if (content) {
        element.innerHTML = content;
    } else {
        element.innerHTML = `<p style="color: var(--text-secondary);">${t('noData')}</p>`;
    }
}

// ==================== 过滤和搜索 ==================== //
function filterPapers(papers) {
    let filtered = papers;
    
    // 按类别过滤
    if (state.selectedCategory) {
        filtered = filtered.filter(paper => 
            paper.categories && paper.categories.includes(state.selectedCategory)
        );
    }
    
    // 按搜索关键词过滤
    if (state.searchQuery) {
        const query = state.searchQuery.toLowerCase();
        filtered = filtered.filter(paper => 
            (paper.title && paper.title.toLowerCase().includes(query)) ||
            (paper.abstract && paper.abstract.toLowerCase().includes(query)) ||
            (paper.authors && paper.authors.some(author => author.toLowerCase().includes(query)))
        );
    }
    
    return filtered;
}

function filterByCategory(category) {
    state.selectedCategory = category;
    state.currentPage = 1;
    
    // 更新侧边栏类别高亮
    document.querySelectorAll('.category-item').forEach(item => {
        item.classList.toggle('active', item.dataset.category === category);
    });
    
    // 更新下拉框
    const select = document.getElementById('paper-category-filter');
    if (select) {
        select.value = category;
    }
    
    // 重新渲染论文
    renderPapers(filterPapers(state.allPapers));
}

function searchPapers(query) {
    state.searchQuery = query;
    state.currentPage = 1;
    renderPapers(filterPapers(state.allPapers));
}

// ==================== 事件监听 ==================== //
function initEventListeners() {
    // 主题切换
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', toggleTheme);
    }
    
    // 搜索
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        let searchTimeout;
        searchInput.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                searchPapers(e.target.value);
            }, 300);
        });
    }
    
    // 类别筛选
    const categoryFilter = document.getElementById('paper-category-filter');
    if (categoryFilter) {
        categoryFilter.addEventListener('change', (e) => {
            filterByCategory(e.target.value);
        });
    }
    
    // 每页显示数量
    const perPageSelect = document.getElementById('papers-per-page');
    if (perPageSelect) {
        perPageSelect.addEventListener('change', (e) => {
            state.papersPerPage = parseInt(e.target.value);
            loadPapers(1);
        });
    }
    
    // 排序
    const sortSelect = document.getElementById('paper-sort');
    if (sortSelect) {
        sortSelect.addEventListener('change', (e) => {
            sortPapers(e.target.value);
        });
    }
}

function sortPapers(sortBy) {
    const papers = [...state.allPapers];
    
    switch (sortBy) {
        case 'date':
            papers.sort((a, b) => new Date(b.published) - new Date(a.published));
            break;
        case 'title':
            papers.sort((a, b) => a.title.localeCompare(b.title));
            break;
        // Add more sort options as needed
    }
    
    state.allPapers = papers;
    renderPapers(filterPapers(papers));
}

// ==================== 滚动行为 ==================== //
function initScrollBehavior() {
    const backToTop = document.getElementById('back-to-top');
    
    window.addEventListener('scroll', () => {
        if (window.pageYOffset > 300) {
            backToTop.classList.add('visible');
        } else {
            backToTop.classList.remove('visible');
        }
    });
    
    backToTop.addEventListener('click', () => {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });
}

// ==================== 工具函数 ==================== //
function updateElement(id, value) {
    const element = document.getElementById(id);
    if (element) {
        element.textContent = value;
    }
}

function showLoading(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = `
            <div class="loading">
                <div class="spinner"></div>
                <p>${t('loading')}</p>
            </div>
        `;
    }
}

function showError(elementId, message) {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = `
            <p style="text-align: center; color: var(--accent-color); padding: 2rem;">
                <i class="fas fa-exclamation-circle"></i> ${message}
            </p>
        `;
    }
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ==================== 导出 ==================== //
window.dailyArxiv = {
    navigateToSection,
    filterByCategory,
    searchPapers,
    loadPapers,
    toggleTheme
};
