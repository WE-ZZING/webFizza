document.addEventListener('DOMContentLoaded', function () {
    const contentDiv = document.getElementById('content');
    const reportButton = document.getElementById('report-button');
    const secureCodeButton = document.getElementById('secure-code-button');

    // 기본적으로 Report 페이지 로드
    loadMarkdown('/report/api/md-file/');

    reportButton?.addEventListener('click', () => {
        loadMarkdown('/report/api/md-file/');d
    });

    // Markdown 파일 로드 및 데이터 처리
    function loadMarkdown(file) {
        fetch(file)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Failed to load the markdown file');
                }
                return response.text();
            })
            .then(mdContent => {
                const vulnerabilityTypes = ['Stored XSS', 'Reflected XSS', 'DOM Based XSS', 'sqli'];

                const vulnerabilityCounts = vulnerabilityTypes.reduce((acc, type) => {
                    const regex = new RegExp(type, 'g');
                    const count = (mdContent.match(regex) || []).length;
                    acc[type] = count;
                    return acc;
                }, {});

                const maxCount = Math.max(...Object.values(vulnerabilityCounts));

                // 취약점 요약 게이지 생성
                const vulnerabilitySummary = document.querySelector('.vulnerability-summary');
                vulnerabilitySummary.innerHTML = '';
                Object.keys(vulnerabilityCounts).forEach(vulnerability => {
                    const gaugeItem = document.createElement('div');
                    gaugeItem.classList.add('gauge-item');
                    
                    gaugeItem.innerHTML = `
                        <div class="gauge-label">${vulnerability}</div>
                        <div class="gauge">
                            <div class="gauge-fill" style="width: ${(vulnerabilityCounts[vulnerability] / maxCount) * 100}%;"></div>
                        </div>
                        <div class="gauge-count">${vulnerabilityCounts[vulnerability]}</div>
                    `;
                    vulnerabilitySummary.appendChild(gaugeItem);
                });

                // 테이블 데이터 처리
                const lines = mdContent.split('\n');
                const tableLines = lines.slice(2);
                const tableRegex = /(\|.*\|)/g;
                const tableMatch = tableLines.join('\n').match(tableRegex);

                if (tableMatch) {
                    const reportData = tableMatch.map(row => {
                        const columns = row.split('|').map(col => col.trim()).filter(col => col.length > 0);
                        return {
                            severity: columns[0],
                            payload: columns[1],
                            vulnerability: columns[2],
                            method: columns[3],
                            url: columns[4],
                            statusCode: columns[5]
                        };
                    });

                    const tbody = document.querySelector('table tbody');
                    tbody.innerHTML = '';
                    reportData.forEach(row => {
                        const tr = document.createElement('tr');
                        tr.innerHTML = `
                            <td><input type="checkbox"></td>
                            <td><span class="severity severity-${row.severity.toLowerCase()}">${row.severity}</span></td>
                            <td>${escapeHtml(row.payload)}</td>
                            <td>${escapeHtml(row.vulnerability)}</td>
                            <td>${escapeHtml(row.method)}</td>
                            <td>${escapeHtml(row.url)}</td>
                            <td>${escapeHtml(row.statusCode)}</td>
                        `;
                        tbody.appendChild(tr);
                    });

                    const selectAllCheckbox = document.getElementById('select-all');
                    selectAllCheckbox.addEventListener('change', function () {
                        const checkboxes = tbody.querySelectorAll('input[type="checkbox"]');
                        checkboxes.forEach(checkbox => {
                            checkbox.checked = selectAllCheckbox.checked;
                        });
                    });
                } else {
                    contentDiv.innerHTML = '<p>No table content found in the report.</p>';
                }

                // 도넛 차트 생성
                const totalVulnerabilities = Object.values(vulnerabilityCounts).reduce((acc, count) => acc + count, 0);
                const pieData = {
                    labels: Object.keys(vulnerabilityCounts),
                    datasets: [{
                        label: 'Vulnerability Breakdown',
                        data: Object.values(vulnerabilityCounts).map(count => (count / totalVulnerabilities) * 100),
                        backgroundColor: ['#5D72E4', '#8A99E1', '#B7C7ED', '#CED4DA'],
                    }]
                };

                const ctxPie = document.getElementById('vulnerabilityPieChart').getContext('2d');
                const vulnerabilityPieChart = new Chart(ctxPie, {
                    type: 'doughnut',
                    data: pieData,
                    options: {
                        responsive: true,
                        maintainAspectRatio: true, // 차트 비율 유지
                        cutout: '60%', // 도넛의 두께
                        plugins: {
                            legend: {
                                position: 'right', // 범례 위치를 오른쪽으로 이동
                                labels: {
                                    boxWidth: 20,
                                    padding: 10,
                                    color: '#343a40'
                                }
                            },
                            tooltip: {
                                callbacks: {
                                    label: function(tooltipItem) {
                                        return `${tooltipItem.label}: ${tooltipItem.raw.toFixed(2)}%`;
                                    }
                                }
                            }
                        }
                    }
                });
            })
            .catch(error => {
                console.error('Error loading the markdown file:', error);
                contentDiv.innerHTML = '<p>Error loading content. Please try again later.</p>';
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

document.querySelector('.view-patch-btn').addEventListener('click', () => {
    window.location.href = '/patch'; // 이동할 페이지 URL
});

