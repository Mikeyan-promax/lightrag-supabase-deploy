/**
 * 知识图谱功能禁用覆盖脚本
 * 彻底阻止任何知识图谱相关的功能和数据渲染
 */

// 设置全局禁用标志
window.GRAPH_DISABLED = true;

// 覆盖可能的图谱相关函数
const disabledGraphFunctions = {
  // 禁用图谱数据获取
  fetchGraphData: () => Promise.reject(new Error('Graph functionality is disabled')),
  getGraphLabels: () => Promise.reject(new Error('Graph functionality is disabled')),
  
  // 禁用图谱渲染
  renderGraph: () => {
    console.warn('Graph rendering is disabled');
    return null;
  },
  
  // 禁用图谱组件
  GraphComponent: () => null,
  KnowledgeGraph: () => null,
  
  // 禁用图谱相关的状态管理
  useGraphStore: () => ({
    nodes: [],
    edges: [],
    isLoading: false,
    error: 'Graph functionality is disabled'
  })
};

// 将禁用函数挂载到全局对象
Object.assign(window, disabledGraphFunctions);

// 拦截React组件渲染
if (window.React) {
  const originalCreateElement = window.React.createElement;
  window.React.createElement = function(type, props, ...children) {
    // 如果是图谱相关组件，返回禁用提示
    if (typeof type === 'string' && 
        (type.toLowerCase().includes('graph') || 
         type.toLowerCase().includes('knowledge'))) {
      return originalCreateElement('div', {
        style: {
          padding: '20px',
          textAlign: 'center',
          color: '#666',
          border: '1px dashed #ccc',
          borderRadius: '8px',
          margin: '10px'
        }
      }, '知识图谱功能已禁用');
    }
    
    if (typeof type === 'function' && type.name && 
        (type.name.toLowerCase().includes('graph') || 
         type.name.toLowerCase().includes('knowledge'))) {
      return originalCreateElement('div', {
        style: {
          padding: '20px',
          textAlign: 'center',
          color: '#666',
          border: '1px dashed #ccc',
          borderRadius: '8px',
          margin: '10px'
        }
      }, '知识图谱功能已禁用');
    }
    
    return originalCreateElement.apply(this, arguments);
  };
}

// 拦截可能的图谱数据请求
const originalXMLHttpRequest = window.XMLHttpRequest;
window.XMLHttpRequest = function() {
  const xhr = new originalXMLHttpRequest();
  const originalOpen = xhr.open;
  
  xhr.open = function(method, url, ...args) {
    if (typeof url === 'string' && 
        (url.includes('/graph') || url.includes('/graphs') || 
         url.includes('knowledge') || url.includes('entity') || 
         url.includes('relation'))) {
      throw new Error('Graph functionality is disabled');
    }
    return originalOpen.apply(this, [method, url, ...args]);
  };
  
  return xhr;
};

// 监听DOM变化，移除可能的图谱元素
const observer = new MutationObserver(function(mutations) {
  mutations.forEach(function(mutation) {
    mutation.addedNodes.forEach(function(node) {
      if (node.nodeType === 1) { // Element node
        const element = node;
        
        // 检查是否是图谱相关元素
        if (element.className && typeof element.className === 'string') {
          if (element.className.toLowerCase().includes('graph') ||
              element.className.toLowerCase().includes('knowledge') ||
              element.className.toLowerCase().includes('sigma') ||
              element.className.toLowerCase().includes('cytoscape')) {
            
            // 替换为禁用提示
            element.innerHTML = `
              <div style="
                padding: 40px;
                text-align: center;
                color: #666;
                border: 2px dashed #ccc;
                border-radius: 12px;
                margin: 20px;
                background: #f9f9f9;
              ">
                <h3>⚠️ 知识图谱功能已禁用</h3>
                <p>当前系统配置下，知识图谱功能不可用。</p>
                <p>请使用文档管理和检索功能。</p>
              </div>
            `;
          }
        }
        
        // 检查文本内容
        if (element.textContent && 
            (element.textContent.includes('Knowledge Graph') ||
             element.textContent.includes('知识图谱'))) {
          
          // 如果是导航标签或按钮，隐藏它
          if (element.tagName === 'BUTTON' || 
              element.getAttribute('role') === 'tab' ||
              element.tagName === 'A') {
            element.style.display = 'none';
          }
        }
      }
    });
  });
});

// 开始观察DOM变化
observer.observe(document.body, {
  childList: true,
  subtree: true
});

// 监听所有点击事件，特别针对Knowledge Graph按钮
document.addEventListener('click', function(e) {
  const target = e.target;
  const text = target.textContent || target.innerText || '';
  const className = target.className || '';
  
  // 检查是否点击了Knowledge Graph相关元素
  if (text.includes('Knowledge Graph') || text.includes('知识图谱') || 
      text.includes('Graph') || className.includes('graph') ||
      target.getAttribute('data-value') === 'graph' ||
      target.closest('[data-value="graph"]') ||
      target.closest('button[role="tab"]') && text.includes('Graph')) {
    
    e.preventDefault();
    e.stopPropagation();
    e.stopImmediatePropagation();
    
    console.log('Graph-related click intercepted, redirecting to disabled page');
    window.location.href = './graph-disabled.html';
    return false;
  }
}, true); // 使用捕获阶段

console.log('Graph functionality has been completely disabled');