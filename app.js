// Initial data from CSV
let projects = [
    {
        no: 1,
        custName: "TMLI",
        pmo: "Completed",
        rmTicket: "5101 / 651870",
        completeDate: "",
        projectTier: "☆☆☆☆☆",
        projectName: "Phase 4 DR",
        techPoint: "35%",
        custPoint: "40%",
        timePoint: "10%",
        totalCust: "85%",
        avgBar: "",
        engineer1: "Dio",
        engineer2: "",
        link: "https://mdrive.mov.co.id/index.php/apps/files/?dir=/Dept-Cloud/01%20-%20Customer/Paid%20Customer/AWS%20Customer/20.%20Tokio%20Marine&fileid=687909"
    },
    {
        no: 2,
        custName: "Dharma Satya Nusantara",
        pmo: "Completed",
        rmTicket: "5160",
        completeDate: "",
        projectTier: "☆☆☆☆☆",
        projectName: "New Development Application on AWS",
        techPoint: "35%",
        custPoint: "50%",
        timePoint: "25%",
        totalCust: "37%",
        avgBar: "",
        engineer1: "Danu",
        engineer2: "Fahmi",
        link: ""
    },
    {
        no: 3,
        custName: "Sayap Mas Utama",
        pmo: "Completed",
        rmTicket: "6257 / 722237",
        completeDate: "",
        projectTier: "☆☆☆☆☆",
        projectName: "Forti on AWS",
        techPoint: "50%",
        custPoint: "50%",
        timePoint: "50%",
        totalCust: "50%",
        avgBar: "",
        engineer1: "Gading",
        engineer2: "",
        link: ""
    },
    {
        no: 4,
        custName: "Sayap Mas Utama",
        pmo: "Cancelled",
        rmTicket: "6559",
        completeDate: "",
        projectTier: "☆☆☆☆☆",
        projectName: "SAP",
        techPoint: "0%",
        custPoint: "0%",
        timePoint: "0%",
        totalCust: "0%",
        avgBar: "",
        engineer1: "Farhan",
        engineer2: "",
        link: ""
    },
    {
        no: 5,
        custName: "Mitech TMS",
        pmo: "Completed",
        rmTicket: "6612 / -",
        completeDate: "",
        projectTier: "☆☆☆☆☆",
        projectName: "IOT",
        techPoint: "35%",
        custPoint: "35%",
        timePoint: "50%",
        totalCust: "40%",
        avgBar: "",
        engineer1: "Dio",
        engineer2: "",
        link: "https://mdrive.mov.co.id/index.php/apps/files/?dir=/Dept-Cloud/01%20-%20Customer/POC%20%26%20Implementation/103%20-%20TMS%20MITech&fileid=823619"
    }
];

// Load from localStorage if available
function loadData() {
    const saved = localStorage.getItem('projectData');
    if (saved) {
        projects = JSON.parse(saved);
    }
}

// Save to localStorage
function saveData() {
    localStorage.setItem('projectData', JSON.stringify(projects));
}

// Render table
function renderTable() {
    const tbody = document.getElementById('tableBody');
    tbody.innerHTML = '';
    
    projects.forEach((p, index) => {
        const statusClass = p.pmo === 'Completed' ? 'status-completed' : 
                           p.pmo === 'Cancelled' ? 'status-cancelled' : 'status-progress';
        
        const linkHtml = p.link ? `<a href="${p.link}" target="_blank" class="link-btn">🔗 Open</a>` : '-';
        
        tbody.innerHTML += `
            <tr>
                <td>${p.no}</td>
                <td>${p.custName}</td>
                <td class="${statusClass}">${p.pmo}</td>
                <td>${p.rmTicket || '-'}</td>
                <td>${p.completeDate || '-'}</td>
                <td>${p.projectTier}</td>
                <td>${p.projectName}</td>
                <td>${p.techPoint}</td>
                <td>${p.custPoint}</td>
                <td>${p.timePoint}</td>
                <td>${p.totalCust}</td>
                <td>${p.avgBar || '-'}</td>
                <td>${p.engineer1 || '-'}</td>
                <td>${p.engineer2 || '-'}</td>
                <td>${linkHtml}</td>
                <td class="action-btns">
                    <button class="btn-edit" onclick="editProject(${index})">Edit</button>
                    <button class="btn-delete" onclick="deleteProject(${index})">Hapus</button>
                </td>
            </tr>
        `;
    });
}

// Update stats
function updateStats() {
    const total = projects.length;
    const completed = projects.filter(p => p.pmo === 'Completed').length;
    const cancelled = projects.filter(p => p.pmo === 'Cancelled').length;
    
    const avgCust = projects.reduce((sum, p) => {
        const val = parseInt(p.totalCust) || 0;
        return sum + val;
    }, 0) / (total || 1);
    
    document.getElementById('totalProjects').textContent = total;
    document.getElementById('completedProjects').textContent = completed;
    document.getElementById('cancelledProjects').textContent = cancelled;
    document.getElementById('avgScore').textContent = Math.round(avgCust) + '%';
}


// Modal functions
function openModal() {
    document.getElementById('modal').style.display = 'block';
    document.getElementById('modalTitle').textContent = 'Tambah Project Baru';
    document.getElementById('projectForm').reset();
    document.getElementById('editIndex').value = -1;
}

function closeModal() {
    document.getElementById('modal').style.display = 'none';
}

// Edit project
function editProject(index) {
    const p = projects[index];
    document.getElementById('modal').style.display = 'block';
    document.getElementById('modalTitle').textContent = 'Edit Project';
    document.getElementById('editIndex').value = index;
    
    document.getElementById('custName').value = p.custName;
    document.getElementById('pmo').value = p.pmo;
    document.getElementById('rmTicket').value = p.rmTicket || '';
    document.getElementById('completeDate').value = p.completeDate || '';
    document.getElementById('projectTier').value = p.projectTier;
    document.getElementById('projectName').value = p.projectName;
    document.getElementById('techPoint').value = parseInt(p.techPoint) || '';
    document.getElementById('custPoint').value = parseInt(p.custPoint) || '';
    document.getElementById('timePoint').value = parseInt(p.timePoint) || '';
    document.getElementById('totalCust').value = parseInt(p.totalCust) || '';
    document.getElementById('avgBar').value = parseInt(p.avgBar) || '';
    document.getElementById('engineer1').value = p.engineer1 || '';
    document.getElementById('engineer2').value = p.engineer2 || '';
    document.getElementById('link').value = p.link || '';
}

// Delete project
function deleteProject(index) {
    if (confirm('Yakin ingin menghapus project ini?')) {
        projects.splice(index, 1);
        // Renumber
        projects.forEach((p, i) => p.no = i + 1);
        saveData();
        renderTable();
        updateStats();
    }
}

// Form submit
document.getElementById('projectForm').addEventListener('submit', function(e) {
    e.preventDefault();
    
    const editIndex = parseInt(document.getElementById('editIndex').value);
    
    const projectData = {
        no: editIndex >= 0 ? projects[editIndex].no : projects.length + 1,
        custName: document.getElementById('custName').value,
        pmo: document.getElementById('pmo').value,
        rmTicket: document.getElementById('rmTicket').value,
        completeDate: document.getElementById('completeDate').value,
        projectTier: document.getElementById('projectTier').value,
        projectName: document.getElementById('projectName').value,
        techPoint: document.getElementById('techPoint').value ? document.getElementById('techPoint').value + '%' : '0%',
        custPoint: document.getElementById('custPoint').value ? document.getElementById('custPoint').value + '%' : '0%',
        timePoint: document.getElementById('timePoint').value ? document.getElementById('timePoint').value + '%' : '0%',
        totalCust: document.getElementById('totalCust').value ? document.getElementById('totalCust').value + '%' : '0%',
        avgBar: document.getElementById('avgBar').value ? document.getElementById('avgBar').value + '%' : '',
        engineer1: document.getElementById('engineer1').value,
        engineer2: document.getElementById('engineer2').value,
        link: document.getElementById('link').value
    };
    
    if (editIndex >= 0) {
        projects[editIndex] = projectData;
    } else {
        projects.push(projectData);
    }
    
    saveData();
    renderTable();
    updateStats();
    closeModal();
});

// Close modal on outside click
window.onclick = function(e) {
    const modal = document.getElementById('modal');
    if (e.target === modal) {
        closeModal();
    }
};

// Initialize
loadData();
renderTable();
updateStats();
