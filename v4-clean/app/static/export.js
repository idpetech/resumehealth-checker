/**
 * Export functionality for Resume Health Checker
 * Handles PDF and DOCX exports from embedded results
 */

function exportToPDF(analysisId) {
    if (!analysisId) {
        alert('Analysis ID is required for PDF export');
        return;
    }
    
    console.log(`Exporting PDF for analysis: ${analysisId}`);
    
    // Show loading state
    const button = event.target;
    const originalText = button.textContent;
    button.textContent = '📄 Generating PDF...';
    button.disabled = true;
    
    // Create download link
    const downloadUrl = `/api/v1/export/${analysisId}/pdf`;
    
    // Create temporary link and trigger download
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = `analysis-${analysisId}.pdf`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    // Restore button state after a short delay
    setTimeout(() => {
        button.textContent = originalText;
        button.disabled = false;
    }, 2000);
}

function exportToDOCX(analysisId) {
    if (!analysisId) {
        alert('Analysis ID is required for DOCX export');
        return;
    }
    
    console.log(`Exporting DOCX for analysis: ${analysisId}`);
    
    // Show loading state
    const button = event.target;
    const originalText = button.textContent;
    button.textContent = '📝 Generating DOCX...';
    button.disabled = true;
    
    // Create download link
    const downloadUrl = `/api/v1/export/${analysisId}/docx`;
    
    // Create temporary link and trigger download
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = `analysis-${analysisId}.docx`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    // Restore button state after a short delay
    setTimeout(() => {
        button.textContent = originalText;
        button.disabled = false;
    }, 2000);
}

// Alternative implementation using fetch for better error handling
async function exportToPDFWithFetch(analysisId) {
    if (!analysisId) {
        alert('Analysis ID is required for PDF export');
        return;
    }
    
    console.log(`Exporting PDF for analysis: ${analysisId}`);
    
    // Show loading state
    const button = event.target;
    const originalText = button.textContent;
    button.textContent = '📄 Generating PDF...';
    button.disabled = true;
    
    try {
        const response = await fetch(`/api/v1/export/${analysisId}/pdf`);
        
        if (!response.ok) {
            throw new Error(`Export failed: ${response.status} ${response.statusText}`);
        }
        
        // Get the filename from the response headers
        const contentDisposition = response.headers.get('Content-Disposition');
        let filename = `analysis-${analysisId}.pdf`;
        if (contentDisposition) {
            const match = contentDisposition.match(/filename="?([^"]+)"?/);
            if (match) {
                filename = match[1];
            }
        }
        
        // Convert response to blob
        const blob = await response.blob();
        
        // Create download link
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        // Clean up
        window.URL.revokeObjectURL(url);
        
    } catch (error) {
        console.error('PDF export error:', error);
        alert(`PDF export failed: ${error.message}`);
    } finally {
        // Restore button state
        button.textContent = originalText;
        button.disabled = false;
    }
}

async function exportToDOCXWithFetch(analysisId) {
    if (!analysisId) {
        alert('Analysis ID is required for DOCX export');
        return;
    }
    
    console.log(`Exporting DOCX for analysis: ${analysisId}`);
    
    // Show loading state
    const button = event.target;
    const originalText = button.textContent;
    button.textContent = '📝 Generating DOCX...';
    button.disabled = true;
    
    try {
        const response = await fetch(`/api/v1/export/${analysisId}/docx`);
        
        if (!response.ok) {
            throw new Error(`Export failed: ${response.status} ${response.statusText}`);
        }
        
        // Get the filename from the response headers
        const contentDisposition = response.headers.get('Content-Disposition');
        let filename = `analysis-${analysisId}.docx`;
        if (contentDisposition) {
            const match = contentDisposition.match(/filename="?([^"]+)"?/);
            if (match) {
                filename = match[1];
            }
        }
        
        // Convert response to blob
        const blob = await response.blob();
        
        // Create download link
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        // Clean up
        window.URL.revokeObjectURL(url);
        
    } catch (error) {
        console.error('DOCX export error:', error);
        alert(`DOCX export failed: ${error.message}`);
    } finally {
        // Restore button state
        button.textContent = originalText;
        button.disabled = false;
    }
}

// Make functions available globally
window.exportToPDF = exportToPDF;
window.exportToDOCX = exportToDOCX;
window.exportToPDFWithFetch = exportToPDFWithFetch;
window.exportToDOCXWithFetch = exportToDOCXWithFetch;
