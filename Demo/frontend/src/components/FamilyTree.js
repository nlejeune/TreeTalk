import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';

const FamilyTree = ({ data, onPersonSelect, selectedPerson }) => {
  const svgRef = useRef();

  useEffect(() => {
    if (!data || !data.nodes || !data.links) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove(); // Clear previous render

    const width = 800;
    const height = 600;
    const margin = { top: 20, right: 20, bottom: 20, left: 20 };

    svg.attr('width', width).attr('height', height);

    // Create main group for zooming and panning
    const g = svg.append('g');

    // Add zoom behavior
    const zoom = d3.zoom()
      .scaleExtent([0.1, 4])
      .on('zoom', (event) => {
        g.attr('transform', event.transform);
      });

    svg.call(zoom);

    // Create force simulation
    const simulation = d3.forceSimulation(data.nodes)
      .force('link', d3.forceLink(data.links).id(d => d.id).distance(120))
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(40));

    // Add links
    const links = g.append('g')
      .attr('class', 'links')
      .selectAll('line')
      .data(data.links)
      .enter()
      .append('line')
      .attr('stroke', d => d.type === 'spouse' ? '#e53e3e' : '#718096')
      .attr('stroke-width', d => d.type === 'spouse' ? 3 : 2)
      .attr('stroke-dasharray', d => d.type === 'spouse' ? '5,5' : 'none');

    // Add nodes
    const nodes = g.append('g')
      .attr('class', 'nodes')
      .selectAll('.node')
      .data(data.nodes)
      .enter()
      .append('g')
      .attr('class', 'node')
      .style('cursor', 'pointer')
      .call(d3.drag()
        .on('start', dragstarted)
        .on('drag', dragged)
        .on('end', dragended));

    // Add circles for persons
    nodes.append('circle')
      .attr('r', 25)
      .attr('fill', d => {
        if (selectedPerson && d.id === selectedPerson.id) return '#667eea';
        return d.gender === 'M' ? '#4299e1' : '#ed64a6';
      })
      .attr('stroke', '#fff')
      .attr('stroke-width', 3)
      .style('filter', 'drop-shadow(2px 2px 4px rgba(0,0,0,0.3))');

    // Add names
    nodes.append('text')
      .text(d => d.firstName)
      .attr('text-anchor', 'middle')
      .attr('dy', '0.35em')
      .attr('fill', 'white')
      .attr('font-size', '11px')
      .attr('font-weight', 'bold')
      .style('pointer-events', 'none');

    // Add birth year below the circle
    nodes.append('text')
      .text(d => {
        if (d.birthDate) {
          const year = new Date(d.birthDate).getFullYear();
          return d.deathDate ? `${year}-${new Date(d.deathDate).getFullYear()}` : `${year}-`;
        }
        return '';
      })
      .attr('text-anchor', 'middle')
      .attr('dy', '45px')
      .attr('fill', '#4a5568')
      .attr('font-size', '10px')
      .style('pointer-events', 'none');

    // Add click handler
    nodes.on('click', (event, d) => {
      event.stopPropagation();
      onPersonSelect && onPersonSelect(d);
      
      // Update node colors
      nodes.select('circle')
        .attr('fill', node => {
          if (d.id === node.id) return '#667eea';
          return node.gender === 'M' ? '#4299e1' : '#ed64a6';
        });
    });

    // Add hover effects
    nodes.on('mouseover', function(event, d) {
      d3.select(this).select('circle')
        .transition()
        .duration(150)
        .attr('r', 28);
      
      // Show tooltip
      const tooltip = d3.select('body').append('div')
        .attr('class', 'tooltip')
        .style('position', 'absolute')
        .style('background', '#2d3748')
        .style('color', 'white')
        .style('padding', '8px 12px')
        .style('border-radius', '6px')
        .style('font-size', '12px')
        .style('pointer-events', 'none')
        .style('opacity', 0)
        .style('z-index', 1000);
      
      tooltip.html(`
        <strong>${d.name}</strong><br/>
        ${d.birthDate ? `Born: ${d.birthDate}` : ''}<br/>
        ${d.deathDate ? `Died: ${d.deathDate}` : 'Still alive'}
      `)
        .style('left', (event.pageX + 10) + 'px')
        .style('top', (event.pageY - 10) + 'px')
        .transition()
        .duration(200)
        .style('opacity', 1);
    })
    .on('mouseout', function(event, d) {
      d3.select(this).select('circle')
        .transition()
        .duration(150)
        .attr('r', 25);
      
      d3.selectAll('.tooltip').remove();
    });

    // Update positions on simulation tick
    simulation.on('tick', () => {
      links
        .attr('x1', d => d.source.x)
        .attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x)
        .attr('y2', d => d.target.y);

      nodes.attr('transform', d => `translate(${d.x},${d.y})`);
    });

    // Drag functions
    function dragstarted(event) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      event.subject.fx = event.subject.x;
      event.subject.fy = event.subject.y;
    }

    function dragged(event) {
      event.subject.fx = event.x;
      event.subject.fy = event.y;
    }

    function dragended(event) {
      if (!event.active) simulation.alphaTarget(0);
      event.subject.fx = null;
      event.subject.fy = null;
    }

    // Add legend
    const legend = svg.append('g')
      .attr('class', 'legend')
      .attr('transform', 'translate(20, 20)');

    const legendData = [
      { color: '#4299e1', label: 'Male', type: 'circle' },
      { color: '#ed64a6', label: 'Female', type: 'circle' },
      { color: '#718096', label: 'Parent-Child', type: 'line' },
      { color: '#e53e3e', label: 'Marriage', type: 'line' }
    ];

    const legendItems = legend.selectAll('.legend-item')
      .data(legendData)
      .enter()
      .append('g')
      .attr('class', 'legend-item')
      .attr('transform', (d, i) => `translate(0, ${i * 25})`);

    legendItems.each(function(d, i) {
      const item = d3.select(this);
      
      if (d.type === 'circle') {
        item.append('circle')
          .attr('r', 8)
          .attr('fill', d.color)
          .attr('stroke', '#fff')
          .attr('stroke-width', 2);
      } else {
        item.append('line')
          .attr('x1', -8)
          .attr('x2', 8)
          .attr('y1', 0)
          .attr('y2', 0)
          .attr('stroke', d.color)
          .attr('stroke-width', 3)
          .attr('stroke-dasharray', d.color === '#e53e3e' ? '3,3' : 'none');
      }
      
      item.append('text')
        .text(d.label)
        .attr('x', 20)
        .attr('dy', '0.35em')
        .attr('font-size', '12px')
        .attr('fill', '#4a5568');
    });

    // Add background rectangle for legend
    const legendBox = legend.node().getBBox();
    legend.insert('rect', ':first-child')
      .attr('x', legendBox.x - 10)
      .attr('y', legendBox.y - 10)
      .attr('width', legendBox.width + 20)
      .attr('height', legendBox.height + 20)
      .attr('fill', 'rgba(255,255,255,0.9)')
      .attr('stroke', '#e2e8f0')
      .attr('stroke-width', 1)
      .attr('rx', 6);

    // Cleanup function
    return () => {
      d3.selectAll('.tooltip').remove();
    };
  }, [data, selectedPerson, onPersonSelect]);

  return (
    <div className="tree-container">
      <svg ref={svgRef}></svg>
      <div style={{
        position: 'absolute',
        bottom: '10px',
        right: '10px',
        background: 'rgba(255,255,255,0.9)',
        padding: '8px 12px',
        borderRadius: '6px',
        fontSize: '12px',
        color: '#718096'
      }}>
        💡 Click nodes to select • Drag to move • Scroll to zoom
      </div>
    </div>
  );
};

export default FamilyTree;