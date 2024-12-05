document.addEventListener('DOMContentLoaded', () => {
  const contentDiv = document.getElementById('content');
  const reportButton = document.getElementById('report-button');
  const secureCodeButton = document.getElementById('secure-code-button');

  // 기본적으로 Report 페이지 로드
  loadMarkdown('report.md');

  reportButton.addEventListener('click', () => {
    loadMarkdown('report.md');
  });

  secureCodeButton.addEventListener('click', () => {
    loadPatchContent('patch.md');
  });

  function loadMarkdown(file) {
    fetch(file)
      .then(response => response.text())
      .then(text => {
        const tableRegex = /(\|.*\|)/g; // 테이블 부분만 추출하는 정규식
        const tableMatch = text.match(tableRegex);
        if (tableMatch) {
          const tableContent = tableMatch.join('\n');
          contentDiv.innerHTML = marked.parse(tableContent);
        } else {
          contentDiv.innerHTML = '<p>No table content found in the report.</p>';
        }
      })
      .catch(error => {
        console.error('Error loading the markdown file:', error);
        contentDiv.innerHTML = '<p>Error loading content. Please try again later.</p>';
      });
  }

  function loadPatchContent(file) {
    fetch(file)
      .then(response => response.text())
      .then(text => {
        const suggestedPatches = text.split('## Suggested Patches')[1];
        if (suggestedPatches) {
          const sections = suggestedPatches.split(/(?=##)/g); // ##로 구분된 섹션 분리
          const originalCodeSection = sections.find(section => section.includes('Original Code'));
          const suggestedCodeSection = sections.find(section => section.includes('Suggested Code'));

          // 코드 섹션 추출 및 정리
          const originalCodeLines = (originalCodeSection.replace('## Original Code', '').trim() || '').split('\n');
          const suggestedCodeLines = (suggestedCodeSection.replace('## Suggested Code', '').trim() || '').split('\n');

          // 원본 코드에서 찾을 수 없는 줄을 파란색으로 강조
          const highlightedSuggestedCode = suggestedCodeLines.map(line => {
            const isInOriginalCode = originalCodeLines.some(originalLine => originalLine.trim() === line.trim());
            return isInOriginalCode ? `<span>${line}</span>` : `<span style="color: blue;">${line}</span>`;
          }).join('\n');

          // 제안된 코드에서 찾을 수 없는 줄을 빨간색으로 강조
          const highlightedOriginalCode = originalCodeLines.map(line => {
            const isInSuggestedCode = suggestedCodeLines.some(suggestedLine => suggestedLine.trim() === line.trim());
            return isInSuggestedCode ? `<span>${line}</span>` : `<span style="color: red;">${line}</span>`;
          }).join('\n');

          contentDiv.innerHTML = `
            <div class="code-block-container">
              <h3>Original Code</h3>
              <pre class="code-block original-code">${highlightedOriginalCode}</pre>
            </div>
            <div class="code-block-container">
              <h3>Suggested Code</h3>
              <pre class="code-block suggested-code">${highlightedSuggestedCode}</pre>
            </div>
          `;
        } else {
          contentDiv.innerHTML = '<p>No suggested patches found in the file.</p>';
        }
      })
      .catch(error => {
        console.error('Error loading the markdown file:', error);
        contentDiv.innerHTML = '<p>Error loading content. Please try again later.</p>';
      });
  }
});

