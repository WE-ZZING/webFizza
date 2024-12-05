document.addEventListener('DOMContentLoaded', function () { 
    const contentDiv = document.getElementById('content');
    const reportButton = document.getElementById('report-button');
    const secureCodeButton = document.getElementById('secure-code-button');

    // 기본적으로 Patch 페이지 로드
    loadPatchMarkdown('/patch/api/md-file/patch.md'); // static 폴더 경로 수정
    loadPrivacyPolicyTable('/patch/api/md-file/privacy.md'); // 경로 수정

    reportButton?.addEventListener('click', () => {
        loadPatchMarkdown('/patch/api/md-file/patch.md'); // static 폴더 경로 수정
        loadPrivacyPolicyTable('/patch/api/md-file/privacy.md');
    });

    // Markdown 파일 로드 및 데이터 처리
    function loadPatchMarkdown(file) {
    fetch(file)
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to load the markdown file');
            }
            return response.text();
        })
        .then(mdContent => {
            const originalCodeMatches = mdContent.match(/## Original Code([\s\S]*?)## Suggested Code/g);
            const suggestedCodeMatches = mdContent.match(/## Suggested Code([\s\S]*?)(?=## Original Code|$)/g);

            if (originalCodeMatches && suggestedCodeMatches && originalCodeMatches.length === suggestedCodeMatches.length) {
                const codeSections = originalCodeMatches.map((_, index) => {
                    const originalCode = originalCodeMatches[index].replace(/## Original Code/, '').trim();
                    const suggestedCode = suggestedCodeMatches[index].replace(/## Suggested Code/, '').trim();
                    return { originalCode, suggestedCode };
                });

                // 코드를 HTML로 출력
                const codeSectionsDiv = document.querySelector('.code-sections');
                codeSectionsDiv.innerHTML = codeSections.map(({ originalCode, suggestedCode }) => `
                    <div class="code-pair">
                        <div class="code-block">
                            <h3>Original Code</h3>
                            <pre>${escapeHtml(originalCode)}</pre>
                        </div>
                        <div class="code-block">
                            <h3>Suggested Code</h3>
                            <pre>${escapeHtml(suggestedCode)}</pre>
                        </div>
                    </div>
                `).join('');
            } else {
                contentDiv.innerHTML = '<p>No matching sections found for Original Code and Suggested Code.</p>';
            }
        })
        .catch(error => {
            console.error('Error loading the markdown file:', error);
            contentDiv.innerHTML = '<p>Error loading content. Please try again later.</p>';
        });
    }



    function loadPrivacyPolicyTable(file) {
    const tableDiv = document.getElementById('privacy-policy-table'); // 테이블을 삽입할 대상 지정
    tableDiv.innerHTML = ''; // 기존 내용을 지워서 중복 방지

    fetch(file)
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to load the privacy file');
            }
            return response.text();
        })
        .then(mdContent => {
            const lines = mdContent.split('\n').filter(line => {
                // 빈 줄, 테이블 헤더, 구분선 제거
                return line.trim() !== '' &&
                       line.trim() !== '| violation | policy | details | recommendation |' &&
                       line.trim() !== '| --- | --- | --- | --- |';
            });
            const dataLines = lines.slice(2); // 파일의 첫 두 줄도 제거

            // 데이터 파싱
            const rows = dataLines.map(line => {
                const columns = line.split('|').map(item => item.trim()); // 구분자로 나누고 공백 제거
                if (columns.length === 6) { // 맨 앞과 맨 뒤에 빈 열이 있는 경우
                    columns.shift(); // 첫 번째 빈 열 제거
                    columns.pop(); // 마지막 빈 열 제거
                }
                const [violation, policy, details, recommendation] = columns;
                return { violation, policy, details, recommendation };
            });

            // 테이블 생성
            const table = document.createElement('table');
            table.innerHTML = `
                <thead>
                    <tr>
                        <th>위반 항목</th>
                        <th>위반 조항</th>
                        <th>위반 내용</th>
                        <th>권장 조치</th>
                    </tr>
                </thead>
                <tbody>
                    ${rows.map(row => `
                        <tr>
                            <td>${escapeHtml(row.violation || '')}</td>
                            <td>${escapeHtml(row.policy || '')}</td>
                            <td>${escapeHtml(row.details || '')}</td>
                            <td>${escapeHtml(row.recommendation || '')}</td>
                        </tr>
                    `).join('')}
                </tbody>
            `;
            tableDiv.appendChild(table);
        })
        .catch(error => {
            console.error('Error loading the privacy file:', error);
            tableDiv.innerHTML = '<p>Error loading privacy policies. Please try again later.</p>';
        });
    }



    function escapeHtml(text) {
        return text.replace(/[&<>"']/g, function (match) {
            const escapeChars = {
                '&': '&amp;',
                '<': '&lt;',
                '>': '&gt;',
                '"': '&quot;',
                "'": '&#39;'
            };
            return escapeChars[match];
        });
    }
});
