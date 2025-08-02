// CRM Navigation Functions
function switchSection(sectionName) {
    // Hide all sections with animation
    document.querySelectorAll('.content-section').forEach(section => {
        if (section.classList.contains('active')) {
            section.style.opacity = '0';
            section.style.transform = 'translateY(-20px)';
            setTimeout(() => {
                section.classList.remove('active');
            }, 200);
        }
    });
    
    // Show selected section with animation
    const targetSection = document.getElementById(sectionName + '-section');
    if (targetSection) {
        setTimeout(() => {
            targetSection.classList.add('active');
            setTimeout(() => {
                targetSection.style.opacity = '1';
                targetSection.style.transform = 'translateY(0)';
            }, 50);
        }, 250);
    }
    
    // Update horizontal navigation tabs
    document.querySelectorAll('.nav-tab').forEach(tab => {
        tab.classList.remove('active');
    });
    
    const activeTab = document.querySelector(`.nav-tab[data-section="${sectionName}"]`);
    if (activeTab) {
        activeTab.classList.add('active');
    }
    
    // Legacy support for sidebar nav-items (if any remain)
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });
    
    const activeNavItem = document.querySelector(`.nav-link[data-section="${sectionName}"]`);
    if (activeNavItem) {
        activeNavItem.parentElement.classList.add('active');
    }
}

function goBack() {
    window.history.back();
}

document.addEventListener('DOMContentLoaded', function() {
    // Horizontal Tab Navigation
    document.querySelectorAll('.nav-tab[data-section]').forEach(tab => {
        tab.addEventListener('click', function(e) {
            e.preventDefault();
            const section = this.getAttribute('data-section');
            switchSection(section);
        });
    });
    
    // Legacy support for nav-link (if any remain)
    document.querySelectorAll('.nav-link[data-section]').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const section = this.getAttribute('data-section');
            switchSection(section);
        });
    });

    // Mostrar solo la primera vez por usuario
    window.onload = function() {
        if (localStorage.getItem('welcomeShown')) {
            document.getElementById('welcome-overlay').style.display = 'none';
        } else {
            setTimeout(function() {
                document.getElementById('welcome-overlay').classList.add('hide');
                setTimeout(function() {
                    document.getElementById('welcome-overlay').style.display = 'none';
                }, 600);
            }, 3000);
            localStorage.setItem('welcomeShown', '1');
        }
    };

    // Global municipio management
    let selectedMunicipio = '';
    
    // Function to get current selected municipio
    function getCurrentMunicipio() {
        return selectedMunicipio;
    }
    
    // Function to update all UI elements when municipio changes
    function updateUIForMunicipio(municipio) {
        selectedMunicipio = municipio;
        
        // Update status indicator
        const statusText = document.getElementById('municipio-selected-text');
        const statusContainer = document.querySelector('.municipio-status');
        
        if (municipio) {
            statusText.textContent = getDisplayName(municipio);
            statusContainer.classList.add('selected');
            
            // Hide required messages and enable buttons
            document.querySelectorAll('.municipio-required-msg').forEach(msg => {
                msg.classList.add('hidden');
            });
            
            // Enable all buttons
            enableAllButtons();
            
            // Load options for analysis
            loadAnalysisOptions(municipio);
            
        } else {
            statusText.textContent = 'Ninguno seleccionado';
            statusContainer.classList.remove('selected');
            
            // Show required messages and disable buttons
            document.querySelectorAll('.municipio-required-msg').forEach(msg => {
                msg.classList.remove('hidden');
            });
            
            // Disable all buttons
            disableAllButtons();
            
            // Clear analysis options
            clearAnalysisOptions();
        }
    }
    
    // Function to enable all functionality buttons
    function enableAllButtons() {
        // Consolidación buttons
        document.querySelector('#consolidar-form button[type="submit"]').disabled = false;
        document.getElementById('normalizar-btn').disabled = false;
        
        // Reportes button
        document.getElementById('reporte-btn').disabled = false;
        
        // Analysis buttons
        document.getElementById('anio-select').disabled = false;
        document.getElementById('ciclo-select').disabled = false;
        document.getElementById('promedio-btn').disabled = false;
        document.getElementById('recaudo-cero-btn').disabled = false;
        document.getElementById('valores-negativos-btn').disabled = false;
        document.getElementById('cumplimiento-porcentajes-btn').disabled = false;
        document.getElementById('select-years-btn').disabled = false;
    }
    
    // Function to disable all functionality buttons
    function disableAllButtons() {
        // Consolidación buttons
        document.querySelector('#consolidar-form button[type="submit"]').disabled = true;
        document.getElementById('normalizar-btn').disabled = true;
        
        // Reportes button
        document.getElementById('reporte-btn').disabled = true;
        
        // Analysis buttons
        document.getElementById('anio-select').disabled = true;
        document.getElementById('ciclo-select').disabled = true;
        document.getElementById('promedio-btn').disabled = true;
        document.getElementById('recaudo-cero-btn').disabled = true;
        document.getElementById('valores-negativos-btn').disabled = true;
        document.getElementById('cumplimiento-porcentajes-btn').disabled = true;
        document.getElementById('select-years-btn').disabled = true;
    }
    
    // Function to load analysis options (years/cycles)
    function loadAnalysisOptions(municipio) {
        fetch('/opciones_reporte', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ municipio })
        })
        .then(r => r.json())
        .then(data => {
            const anioSelect = document.getElementById('anio-select');
            const cicloSelect = document.getElementById('ciclo-select');
            
            anioSelect.innerHTML = '<option value="todos">Todos</option>';
            if (data.anios) data.anios.forEach(a => {
                anioSelect.innerHTML += `<option value="${a}">${a}</option>`;
            });
            
            cicloSelect.innerHTML = '<option value="todos">Todos</option>';
            if (data.ciclos) data.ciclos.forEach(c => {
                cicloSelect.innerHTML += `<option value="${c}">${c}</option>`;
            });
        })
        .catch(err => {
            console.error('Error loading analysis options:', err);
        });
    }
    
    // Function to clear analysis options
    function clearAnalysisOptions() {
        document.getElementById('anio-select').innerHTML = '';
        document.getElementById('ciclo-select').innerHTML = '';
    }
    
    // Mapeo de nombres de municipios para mostrar versiones amigables
    const municipioDisplayNames = {
        'Guacarí': 'Bogotá',
        'Jamundí': 'Cali', 
        'El Cerrito': 'Sao Paulo',
        'Quimbaya': 'Rio de Janeiro',
        'Circasia': 'Acapulco',
        'Puerto Asís': 'Puebla',
        'Jericó': 'Medellin',
        'Ciudad Bolívar': 'Cúcuta', 
        'Pueblorico': 'Aracaju',
        'Tarso': 'Tarragona',
        'Santa Bárbara': 'Santa Marta',
        // Puedes cambiar estos nombres por los que prefieras mostrar
    };
    
    // Función para obtener el nombre a mostrar
    function getDisplayName(municipio) {
        return municipioDisplayNames[municipio] || municipio;
    }
    
    // Cargar municipios dinámicamente en el sidebar
    fetch('/municipios')
      .then(r => r.json())
      .then(data => {
        const sidebarSelect = document.getElementById('sidebar-municipio-select');
        data.municipios.forEach(m => {
          const opt = document.createElement('option');
          opt.value = m; // Mantiene el valor original para el backend
          opt.textContent = getDisplayName(m); // Muestra el nombre amigable
          sidebarSelect.appendChild(opt);
        });
      });
    
    // Handle sidebar municipio selection
    document.getElementById('sidebar-municipio-select').addEventListener('change', function() {
        const municipio = this.value;
        updateUIForMunicipio(municipio);
    });

    // Manejar submit del formulario
    const form = document.getElementById('consolidar-form');
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        const municipio = getCurrentMunicipio();
        if (!municipio) return;
        document.getElementById('loader-overlay').style.display = 'flex';
        const loaderMsg = document.getElementById('loader-message');
        loaderMsg.textContent = 'Preparando consolidación...';
        let steps = [
            'Buscando archivos Excel...',
            'Leyendo archivos...',
            'Procesando datos...',
            'Guardando archivos...',
            'Finalizando...'
        ];
        let i = 0;
        const interval = setInterval(() => {
            if (i < steps.length) {
                loaderMsg.textContent = steps[i];
                i++;
            }
        }, 900);
        // Mensaje de advertencia si tarda más de 10 segundos
        let warningTimeout = setTimeout(() => {
            loaderMsg.textContent = 'Esto puede tardar varios minutos si hay muchos datos...';
        }, 10000);
        fetch('/consolidar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ municipio })
        })
        .then(r => r.json())
        .then(data => {
            clearInterval(interval);
            clearTimeout(warningTimeout);
            document.getElementById('loader-overlay').style.display = 'none';
            loaderMsg.textContent = '';
            if (data.error) {
                showToast(data.error, 'error');
            } else {
                showToast('¡Consolidación exitosa!<br>Excel: ' + data.ruta_excel + '<br>DB: ' + data.ruta_db, 'success');
            }
        })
        .catch(err => {
            clearInterval(interval);
            clearTimeout(warningTimeout);
            document.getElementById('loader-overlay').style.display = 'none';
            loaderMsg.textContent = '';
            showToast('Error inesperado', 'error');
        });
    });

    // Normalizar S_TIPO_USO
    const normalizarBtn = document.getElementById('normalizar-btn');
    normalizarBtn.addEventListener('click', function() {
        const municipio = getCurrentMunicipio();
        if (!municipio) return;
        document.getElementById('loader-overlay').style.display = 'flex';
        const loaderMsg = document.getElementById('loader-message');
        loaderMsg.textContent = 'Normalizando S_TIPO_USO...';
        fetch('/normalizar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ municipio })
        })
        .then(response => response.json())
        .then(data => {
            document.getElementById('loader-overlay').style.display = 'none';
            loaderMsg.textContent = '';
            if (data.ok) {
                alert(data.mensaje); // Mensaje de éxito
            } else if (data.error) {
                alert("Error: " + data.error); // Mensaje de error
            }
        })
        .catch(error => {
            document.getElementById('loader-overlay').style.display = 'none';
            loaderMsg.textContent = '';
            alert("Error de comunicación con el servidor. Intenta de nuevo.");
        });
    });

    // Reporte de calidad
    const reporteBtn = document.getElementById('reporte-btn');
    reporteBtn.addEventListener('click', function() {
        const municipio = getCurrentMunicipio();
        if (!municipio) return;
        const panel = document.getElementById('reporte-panel');
        const content = document.getElementById('reporte-content');
        content.innerHTML = '<em>Cargando reporte...</em>';
        mostrarPanel();
        // Hide multianio controls
        document.getElementById('multianio-controls').style.display = 'none';
        fetch('/reporte_calidad', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ municipio })
        })
        .then(r => r.json())
        .then(data => {
            if (data.error) {
                content.innerHTML = '<span style="color:red">' + data.error + '</span>';
            } else {
                let html = '';
                html += '<b>S_CICLO</b><br>';
                html += 'No estándar: <b>' + data.ciclo.no_std_count + '</b><br>';
                html += 'Valores únicos no estándar:<br>';
                if (data.ciclo.unicos.length) {
                    html += '<ul>' + data.ciclo.unicos.map(x => '<li>' + x + '</li>').join('') + '</ul>';
                } else {
                    html += '<i>Ninguno</i><br>';
                }
                html += '<hr><b>S_TIPO_USO</b><br>';
                html += 'No estándar: <b>' + data.tipo_uso.no_std_count + '</b><br>';
                html += 'Valores únicos no estándar:<br>';
                if (data.tipo_uso.unicos.length) {
                    html += '<ul>' + data.tipo_uso.unicos.map(x => '<li>' + x + '</li>').join('') + '</ul>';
                } else {
                    html += '<i>Ninguno</i><br>';
                }
                content.innerHTML = html;
            }
        })
        .catch(err => {
            content.innerHTML = '<span style="color:red">Error inesperado</span>';
        });
    });
    // Función para cerrar panel
    function cerrarPanel() {
        const panel = document.getElementById('reporte-panel');
        const bottomBtn = document.getElementById('cerrar-reporte-bottom');
        panel.classList.remove('show');
        bottomBtn.style.display = 'none';
        setTimeout(() => {
            panel.style.display = 'none';
        }, 300);
    }
    
    // Función para mostrar panel
    function mostrarPanel() {
        const panel = document.getElementById('reporte-panel');
        const bottomBtn = document.getElementById('cerrar-reporte-bottom');
        panel.style.display = 'block';
        bottomBtn.style.display = 'block';
        setTimeout(() => {
            panel.classList.add('show');
        }, 10);
    }
    
    // Event listeners para ambos botones de cerrar
    document.getElementById('cerrar-reporte').onclick = cerrarPanel;
    document.getElementById('cerrar-reporte-bottom').onclick = cerrarPanel;

    // Promedio de consumo
    const promedioBtn = document.getElementById('promedio-btn');
    const anioSelect = document.getElementById('anio-select');
    const cicloSelect = document.getElementById('ciclo-select');
    
    promedioBtn.addEventListener('click', function() {
        const municipio = getCurrentMunicipio();
        const anio = anioSelect.value;
        const ciclo = cicloSelect.value;
        const panel = document.getElementById('reporte-panel');
        const content = document.getElementById('reporte-content');
        content.innerHTML = '<em>Calculando promedios...</em>';
        mostrarPanel();
        // Hide multianio controls
        document.getElementById('multianio-controls').style.display = 'none';
        fetch('/promedio_consumo', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ municipio, anio, ciclo })
        })
        .then(r => r.json())
        .then(data => {
            if (data.error) {
                content.innerHTML = '<span style="color:red">' + data.error + '</span>';
            } else {
                let html = '<b>Promedio de consumo y valores por S_TIPO_USO</b><br>';
                html += `<small>Año: <b>${anio === 'todos' ? 'Todos' : anio}</b> &nbsp;|&nbsp; Ciclo: <b>${ciclo === 'todos' ? 'Todos' : ciclo}</b></small><br><br>`;
                html += '<table border="1" cellpadding="6" style="border-collapse:collapse; width:100%; font-size:1rem;">';
                html += '<tr style="background:#e3eefd;"><th>S_TIPO_USO</th><th>Número de usuarios</th><th>Promedio CANT_KW</th><th>Promedio VR_RECAUDO</th><th>Promedio VR_FACT</th></tr>';
                if (data.resultados && data.resultados.length) {
                    data.resultados.forEach(row => {
                        html += `<tr><td>${row.tipo_uso}</td><td>${row.promedio_cant_kw ?? '-'}</td><td>${row.cantidad}</td><td>${row.promedio_vr_recaudo?.toFixed(2) ?? '-'}</td><td>${row.promedio_vr_fact?.toFixed(2) ?? '-'}</td></tr>`;
                    });
                } else {
                    html += '<tr><td colspan="5"><i>No hay datos</i></td></tr>';
                }
                html += '</table>';
                if (data.analisis && data.analisis.length) {
                    html += '<br><b>Análisis de consumo 0/vacío y datos faltantes</b><br>';
                    html += '<table border="1" cellpadding="6" style="border-collapse:collapse; width:100%; font-size:1rem; margin-top:1em;">';
                    html += '<tr style="background:#fbeee3;"><th>S_TIPO_USO</th><th>Usuarios con consumo 0/vacío</th><th>Periodos faltantes</th></tr>';
                    data.analisis.forEach(row => {
                        html += `<tr><td>${row.tipo_uso}</td><td>${row.consumo_cero}</td><td>${row.faltantes}`;
                        if (row.faltantes > 0 && row.detalle_faltantes && row.detalle_faltantes.length) {
                            html += `<br><small>(${row.detalle_faltantes.join(', ')})</small>`;
                        }
                        html += '</td></tr>';
                    });
                    html += '</table>';
                }
                content.innerHTML = html;
            }
        })
        .catch(err => {
            content.innerHTML = '<span style="color:red">Error inesperado</span>';
        });
    });

    // Recaudo cero
    const recaudoCeroBtn = document.getElementById('recaudo-cero-btn');
    recaudoCeroBtn.addEventListener('click', function() {
        const municipio = getCurrentMunicipio();
        const anio = anioSelect.value;
        const ciclo = cicloSelect.value;
        const panel = document.getElementById('reporte-panel');
        const content = document.getElementById('reporte-content');
        content.innerHTML = '<em>Buscando casos de consumo con recaudo 0...</em>';
        mostrarPanel();
        // Hide multianio controls
        document.getElementById('multianio-controls').style.display = 'none';
        fetch('/reporte_recaudo_cero', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ municipio, anio, ciclo })
        })
        .then(r => r.json())
        .then(data => {
            if (data.error) {
                content.innerHTML = '<span style="color:red">' + data.error + '</span>';
            } else {
                let html = '<b>Casos con VR_RECAUDO = 0</b><br>';
                html += `<small>Año: <b>${anio === 'todos' ? 'Todos' : anio}</b> &nbsp;|&nbsp; Ciclo: <b>${ciclo === 'todos' ? 'Todos' : ciclo}</b></small><br><br>`;
                // Pivot table: periodos como filas, S_TIPO_USO como columnas
                const tipos = ['RESIDENCIAL','COMERCIAL','INDUSTRIAL','OFICIAL'];
                const periodos = [...new Set(data.resultados.map(r => r.periodo))];
                html += '<table border="1" cellpadding="6" style="border-collapse:collapse; width:100%; font-size:1rem;">';
                html += '<tr style="background:#ffe3e3;"><th>Periodo</th>' + tipos.map(t=>`<th>${t}</th>`).join('') + '</tr>';
                if (periodos.length) {
                    periodos.forEach(p => {
                        html += `<tr><td>${p}</td>`;
                        tipos.forEach(t => {
                            const found = data.resultados.find(r => r.periodo===p && r.tipo_uso===t);
                            const val = found ? found.cantidad : 0;
                            if(val>0){
                                html += `<td><b>${val}</b> <button onclick="window.open('','_blank').document.write('Cargando...');fetch('/detalle_recaudo_cero',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({municipio:'${municipio}',anio:'${anio}',ciclo:'${ciclo}',periodo:'${p}',tipo_uso:'${t}'})}).then(r=>r.text()).then(html=>{var w=window.open('','_blank');w.document.write(html);});">Ver</button></td>`;
                            }else{
                                html += `<td>${val}</td>`;
                            }
                        });
                        html += '</tr>';
                    });
                } else {
                    html += '<tr><td colspan="5"><i>No hay datos</i></td></tr>';
                }
                html += '</table>';
                content.innerHTML = html;
            }
        })
        .catch(err => {
            content.innerHTML = '<span style="color:red">Error inesperado</span>';
        });
    });

    // Valores negativos
    const valoresNegBtn = document.getElementById('valores-negativos-btn');
    valoresNegBtn.addEventListener('click', function() {
        const municipio = getCurrentMunicipio();
        const anio = anioSelect.value;
        const ciclo = cicloSelect.value;
        const panel = document.getElementById('reporte-panel');
        const content = document.getElementById('reporte-content');
        content.innerHTML = '<em>Buscando valores negativos...</em>';
        mostrarPanel();
        // Hide multianio controls
        document.getElementById('multianio-controls').style.display = 'none';
        fetch('/reporte_valores_negativos', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ municipio, anio, ciclo })
        })
        .then(r => r.json())
        .then(data => {
            if (data.error) {
                content.innerHTML = '<span style="color:red">' + data.error + '</span>';
            } else {
                let html = '<b>Valores negativos (VR_RECAUDO / VR_FACT)</b><br>';
                html += `<small>Año: <b>${anio === 'todos' ? 'Todos' : anio}</b> &nbsp;|&nbsp; Ciclo: <b>${ciclo === 'todos' ? 'Todos' : ciclo}</b></small><br><br>`;
                const tipos = ['RESIDENCIAL','COMERCIAL','INDUSTRIAL','OFICIAL'];
                const periodos = [...new Set(data.resultados.map(r => r.periodo))];
                html += '<table border="1" cellpadding="6" style="border-collapse:collapse; width:100%; font-size:1rem;">';
                html += '<tr style="background:#e3eefd;"><th rowspan="2">Periodo</th><th colspan="4">VR_RECAUDO &lt; 0</th></tr>';
                html += '<tr>' + tipos.map(t=>`<th>${t}</th>`).join('') + '</tr>';
                periodos.forEach(p => {
                    html += `<tr><td>${p}</td>`;
                    tipos.forEach(t => {
                        const found = data.resultados.find(r => r.periodo===p && r.tipo_uso===t);
                        const val = found ? found.vr_recaudo_neg : 0;
                        if(val>0){
                            html += `<td><b>${val}</b> <button onclick=\"window.open('','_blank').document.write('Cargando...');fetch('/detalle_valores_negativos',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({municipio:'${municipio}',anio:'${anio}',ciclo:'${ciclo}',periodo:'${p}',tipo_uso:'${t}',campo:'VR_RECAUDO'})}).then(r=>r.text()).then(html=>{var w=window.open('','_blank');w.document.write(html);});\">Ver</button></td>`;
                        }else{
                            html += `<td>${val}</td>`;
                        }
                    });
                    html += '</tr>';
                });
                html += '<tr style="background:#e3eefd;"><th rowspan="2">Periodo</th><th colspan="4">VR_FACT &lt; 0</th></tr>';
                html += '<tr>' + tipos.map(t=>`<th>${t}</th>`).join('') + '</tr>';
                periodos.forEach(p => {
                    html += `<tr><td>${p}</td>`;
                    tipos.forEach(t => {
                        const found = data.resultados.find(r => r.periodo===p && r.tipo_uso===t);
                        const val = found ? found.vr_fact_neg : 0;
                        if(val>0){
                            html += `<td><b>${val}</b> <button onclick=\"window.open('','_blank').document.write('Cargando...');fetch('/detalle_valores_negativos',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({municipio:'${municipio}',anio:'${anio}',ciclo:'${ciclo}',periodo:'${p}',tipo_uso:'${t}',campo:'VR_FACT'})}).then(r=>r.text()).then(html=>{var w=window.open('','_blank');w.document.write(html);});\">Ver</button></td>`;
                        }else{
                            html += `<td>${val}</td>`;
                        }
                    });
                    html += '</tr>';
                });
                html += '</table>';
                content.innerHTML = html;
            }
        })
        .catch(err => {
            content.innerHTML = '<span style="color:red">Error inesperado</span>';
        });
    });

   
    // Cumplimiento de porcentajes
    const cumplimientoBtn = document.getElementById('cumplimiento-porcentajes-btn');
    cumplimientoBtn.addEventListener('click', function() {
        const municipio = getCurrentMunicipio();
        const anio = anioSelect.value;
        const ciclo = cicloSelect.value;
        const panel = document.getElementById('reporte-panel');
        const content = document.getElementById('reporte-content');
        content.innerHTML = '<em>Analizando cumplimiento tarifario...</em>';
        mostrarPanel();
        // Hide multianio controls
        document.getElementById('multianio-controls').style.display = 'none';
        fetch('/cumplimiento_porcentajes', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ municipio, anio, ciclo })
        })
        .then(r => r.json())
        .then(data => {
            if (data.error) {
                content.innerHTML = '<span style="color:red">' + data.error + '</span>';
            } else {
                // Prepara los botones de filtrado
                
                const filtrosHtml = `
                  <div class="filtro-botones">
                    <button id="btn-descargar-filtrado" class="btn btn-download" style="display:none;">
                      Descargar filtrado
                    </button>
                  </div>
                `;
                let tipos = data.tipos;
                let periodos = data.periodos;
                let html = '<b>Cumplimiento tarifario</b><br>';
                html += `<small>Año: <b>${anio === 'todos' ? 'Todos' : anio}</b> &nbsp;|&nbsp; Ciclo: <b>${ciclo === 'todos' ? 'Todos' : ciclo}</b></small><br><br>`;
                html += '<table id="tabla-cumplimiento" border="1" cellpadding="6" style="border-collapse:collapse; width:100%; font-size:1rem;">';
                html += '<thead><tr style="background:#e3eefd;"><th>Periodo</th>' + tipos.map(t=>`<th>${t}</th>`).join('') + '</tr></thead>';
                html += '<tbody>';
                if (periodos.length) {
                    periodos.forEach(p => {
                        html += `<tr><td>${p}</td>`;
                        tipos.forEach(t => {
                            const found = data.resultados.find(r => r.periodo===p && r.tipo_uso===t);
                            const totalNoCumplen = found ? found.total_no_cumplen : 0;
                            if(totalNoCumplen > 0){
                                html += `<td><b>${totalNoCumplen}</b> <button onclick=\"window.open('','_blank').document.write('Cargando...');fetch('/detalle_cumplimiento_porcentajes',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({municipio:'${municipio}',anio:'${anio}',ciclo:'${ciclo}',periodo:'${p}',tipo_uso:'${t}'})}).then(r=>r.text()).then(html=>{var w=window.open('','_blank');w.document.write(html);});\">Ver</button></td>`;
                            }else{
                                html += `<td>${totalNoCumplen}</td>`;
                            }
                        });
                        html += '</tr>';
                    });
                } else {
                    html += '<tr><td colspan="' + (tipos.length + 1) + '"><i>No hay datos</i></td></tr>';
                }
                html += '</tbody></table>';
                // Inserta los botones y la tabla
                content.innerHTML = filtrosHtml + html;
                // --- Inicializar filtros ---
                const tabla = document.getElementById('tabla-cumplimiento');
                const tbody = tabla.querySelector('tbody');
                const filasOriginales = Array.from(tbody.rows);
                function filtrarTabla(filtroFn) {
                  tbody.innerHTML = '';
                  const filtradas = filasOriginales.filter(filtroFn);
                  filtradas.forEach(f => tbody.appendChild(f));
                  document.getElementById('btn-descargar-filtrado')
                          .style.display = filtradas.length ? 'inline-block' : 'none';
                }
                // Eliminar handlers de los botones de filtrado que ya no existen
                document.getElementById('btn-descargar-filtrado').onclick = () => {
                  descargarTablaComoExcel(tabla, 'resultado_filtrado.xlsx');
                };
            }
        })
        .catch(err => {
            content.innerHTML = '<span style="color:red">Error inesperado</span>';
        });
    });

    // Función global para generar gráfico de cumplimiento desde el panel
    window.mostrarGraficoCumplimiento = function() {
        // Obtener datos de la tabla en el panel de reporte
        const panel = document.getElementById('reporte-panel');
        if (!panel || panel.style.display === 'none') {
            alert('Primero debe ejecutar el análisis de cumplimiento tarifario');
            return;
        }
        
        const tabla = panel.querySelector('#tabla-cumplimiento');
        if (!tabla) {
            alert('No se encontró la tabla de cumplimiento');
            return;
        }
        
        const filas = tabla.querySelectorAll('tbody tr:not([style*="display: none"])');
        console.log('Filas encontradas:', filas.length);
        
        // Encontrar la posición de la columna TIPO_INCUMPLIMIENTO
        const headers = tabla.querySelectorAll('thead th');
        let tipoColumnIndex = -1;
        headers.forEach((header, index) => {
            if (header.textContent.trim() === 'TIPO_INCUMPLIMIENTO') {
                tipoColumnIndex = index;
            }
        });
        
        console.log('Índice de columna TIPO_INCUMPLIMIENTO:', tipoColumnIndex);
        
        if (tipoColumnIndex === -1) {
            alert('No se encontró la columna TIPO_INCUMPLIMIENTO');
            return;
        }
        
        // Contar por tipo de incumplimiento
        const conteos = {};
        filas.forEach((fila, index) => {
            const tipoCell = fila.querySelector(`td:nth-child(${tipoColumnIndex + 1})`);
            if (tipoCell) {
                const tipo = tipoCell.textContent.trim();
                console.log(`Fila ${index}: ${tipo}`);
                conteos[tipo] = (conteos[tipo] || 0) + 1;
            }
        });
        
        console.log('Conteos:', conteos);
        
        // Mapear nombres más legibles
        const tipoNames = {
            'porcentaje_inferior': 'Porcentaje Inferior',
            'porcentaje_superior': 'Porcentaje Superior', 
            'valor_inferior': 'Valor Inferior',
            'valor_superior': 'Valor Superior',
            'datos_invalidos': 'Datos Inválidos',
            'logica_no_encontrada': 'Lógica No Encontrada',
            'calculo_no_aplicable': 'Cálculo No Aplicable'
        };
        
        if (Object.keys(conteos).length === 0) {
            alert('No se encontraron datos para el gráfico. Verifique que haya registros visibles en la tabla.');
            return;
        }
        
        const labels = Object.keys(conteos).map(k => tipoNames[k] || k);
        const datos = Object.values(conteos);
        const colores = ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40', '#C9CBCF'];
        
        // Crear ventana con gráfico de barras
        const ventana = window.open('', '_blank', 'width=900,height=700,scrollbars=yes,resizable=yes');
        ventana.document.write(`
            <!DOCTYPE html>
            <html>
            <head>
                <title>Gráfico de Incumplimientos</title>
                <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
                <style>
                    body { font-family: Arial, sans-serif; padding: 20px; }
                    .stats { background: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
                    .chart-container { width: 100%; height: 500px; position: relative; }
                </style>
            </head>
            <body>
                <h2>Gráfico de Incumplimientos Tarifarios</h2>
                <div class="stats">
                    <p><strong>Total de registros mostrados:</strong> ${filas.length.toLocaleString()}</p>
                </div>
                <div class="chart-container">
                    <canvas id="graficoBarras"></canvas>
                </div>
                
                <script>
                    const ctx = document.getElementById('graficoBarras').getContext('2d');
                    new Chart(ctx, {
                        type: 'bar',
                        data: {
                            labels: ${JSON.stringify(labels)},
                            datasets: [{
                                label: 'Cantidad de Incumplimientos',
                                data: ${JSON.stringify(datos)},
                                backgroundColor: ${JSON.stringify(colores.slice(0, labels.length))},
                                borderWidth: 1
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: {
                                title: {
                                    display: true,
                                    text: 'Distribución de Tipos de Incumplimiento',
                                    font: { size: 16 }
                                },
                                legend: {
                                    display: false
                                }
                            },
                            scales: {
                                y: {
                                    beginAtZero: true,
                                    ticks: {
                                        stepSize: 1
                                    }
                                }
                            }
                        }
                    });
                </script>
            </body>
            </html>
        `);
    };

    // Utilidad: descargar tabla como Excel (CSV)
    function descargarTablaComoExcel(tabla, nombreArchivo) {
        let csv = '';
        const filas = tabla.querySelectorAll('tr');
        filas.forEach(fila => {
            const cols = Array.from(fila.children).map(td => `"${td.innerText.replace(/"/g, '""')}"`);
            csv += cols.join(',') + '\n';
        });
        const blob = new Blob([csv], {type: 'text/csv'});
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = nombreArchivo;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }

    function showToast(msg, type) {
        alert((type === 'error' ? 'Error: ' : '') + msg.replace(/<[^>]+>/g, ''));
    }

    // 1. Al hacer click en "Seleccionar años", cargar años disponibles
    document.getElementById('select-years-btn').addEventListener('click', () => {
      const municipio = getCurrentMunicipio();
      if (!municipio) {
        alert('Seleccione un municipio primero');
        return;
      }
      // Mostrar el panel y limpiar el contenido
      mostrarPanel();
      document.getElementById('reporte-content').innerHTML = '';
      fetch('/opciones_reporte', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ municipio })
      })
      .then(r => r.json())
      .then(data => {
        const sel = document.getElementById('years-select');
        sel.innerHTML = '';
        data.anios.forEach(a => sel.add(new Option(a, a)));
        document.getElementById('multianio-controls').style.display = 'block';
      });
    });

    // 3. Al pulsar "Calcular promedios multianuales":
    document.getElementById('calcular-promedios-btn').addEventListener('click', () => {
      const selected = Array.from(
        document.getElementById('years-select').selectedOptions
      ).map(o => o.value);
      if (!selected.length) {
        alert('Seleccione al menos un año');
        return;
      }
      const municipio = getCurrentMunicipio();
      const content = document.getElementById('reporte-content');
      content.innerHTML = '<em>Calculando promedios multianuales...</em>';
      mostrarPanel();
      fetch('/promedios_multianio', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ municipio, years: selected })
      })
      .then(r => r.json())
      .then(resp => {
        // Construir tabla
        let html = '<button id="descargar-promedios-btn" class="btn btn-download" style="margin-bottom:1rem;">Descargar Excel</button>';
        html += '<table id="tabla-multianio" border="1" cellpadding="6" style="width:100%; font-size:1rem; border-collapse:collapse;">';
        html += '<thead><tr><th>S_ID</th><th>S_NOMBRE</th><th>S_TIPO_MERCADO</th><th>S_TIPO_USO</th>';
        selected.forEach(y => {
          html += `<th>PROM KW ${y}</th><th>PROM FACT ${y}</th><th>PROM RECAUDO ${y}</th>`;
        });
        if (resp.lastMonth) {
          html += `<th>Consumo KW ${resp.lastMonth.year}-${resp.lastMonth.month}</th><th>Consumo FACT ${resp.lastMonth.year}-${resp.lastMonth.month}</th><th>Consumo RECAUDO ${resp.lastMonth.year}-${resp.lastMonth.month}</th>`;
          html += '<th>PROPORCION DIF CANT_KW</th><th>DIF CANT_KW</th><th>DIF VR_FACT</th><th>DIF VR_REC</th>';
        }
        html += '</tr></thead><tbody>';
        resp.results.forEach(row => {
          html += `<tr><td>${row.s_id}</td><td>${row.s_nombre ?? '-'}</td><td>${row.s_tipo_mercado ?? '-'}</td><td>${row.s_tipo_uso ?? '-'}</td>`;
          selected.forEach(y => {
            const v = row.averages[y] || {};
            html += `<td>${v.kw ?? '-'}</td><td>${v.fact ?? '-'}</td><td>${v.recaudo ?? '-'}</td>`;
          });
          if (resp.lastMonth) {
            const v = row.lastConsumption || {};
            html += `<td>${v.kw ?? '-'}</td><td>${v.fact ?? '-'}</td><td>${v.recaudo ?? '-'}</td>`;
            html += `<td>${row.proporcion_dif_cant_kw ?? '-'}</td><td>${row.dif_cant_kw ?? '-'}</td><td>${row.dif_vr_fact ?? '-'}</td><td>${row.dif_vr_rec ?? '-'}</td>`;
          }
          html += '</tr>';
        });
        html += '</tbody></table>';
        content.innerHTML = html;
        // Handler para descargar Excel real
        document.getElementById('descargar-promedios-btn').onclick = () => {
          fetch('/download_promedios_multianio', {
            method: 'POST',
            headers: { 'Content-Type':'application/json' },
            body: JSON.stringify({ municipio, years: selected })
          })
          .then(r => r.blob())
          .then(blob => {
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'promedios_multianio.xlsx';
            document.body.appendChild(a);
            a.click();
            a.remove();
          });
        };
      })
      .catch(() => {
        content.innerHTML = '<span style="color:red">Error calculando promedios multianuales</span>';
      });
    });
});
