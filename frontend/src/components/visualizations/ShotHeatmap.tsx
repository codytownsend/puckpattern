import React, { useEffect, useRef, useCallback } from 'react';
import * as d3 from 'd3';
import styled from 'styled-components';
import { Box, Typography, Paper, useTheme } from '@mui/material';
import { HeatmapPoint } from '../../store/slices/shotsSlice';

interface ShotHeatmapProps {
  data: HeatmapPoint[];
  width?: number;
  height?: number;
  showLabels?: boolean;
  colorScheme?: string;
  maxValue?: number;
  title?: string;
  onPointClick?: (point: HeatmapPoint) => void;
}

const StyledPaper = styled(Paper)`
  padding: 16px;
  border-radius: 12px;
  box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.05);
`;

const ShotHeatmap: React.FC<ShotHeatmapProps> = ({
  data,
  width = 800,
  height = 400,
  showLabels = true,
  colorScheme = 'blues',
  maxValue,
  title,
  onPointClick,
}) => {
  const theme = useTheme();
  const svgRef = useRef<SVGSVGElement>(null);
  
  // Define color schemes
  const colorSchemes: { [key: string]: string[] } = {
    blues: [theme.palette.primary.light, theme.palette.primary.dark],
    reds: [theme.palette.error.light, theme.palette.error.main],
    greens: [theme.palette.success.light, theme.palette.success.main],
    custom: [theme.palette.primary.light, theme.palette.secondary.main],
  };
  
  // Get the color range based on the selected scheme
  const colorRange = colorSchemes[colorScheme] || colorSchemes.blues;
  
  // Use a callback for onPointClick to avoid dependency issues
  const handlePointClick = useCallback((d: HeatmapPoint, event: Event) => {
    if (onPointClick) {
      event.stopPropagation();
      onPointClick(d);
    }
  }, [onPointClick]);
  
  useEffect(() => {
    if (!data || data.length === 0 || !svgRef.current) return;
    
    // Store a reference to the SVG element for cleanup
    const svgNode = svgRef.current;
    
    // Clear any previous SVG content
    d3.select(svgNode).selectAll('*').remove();
    
    // Set up SVG and margins
    const margin = { top: 20, right: 30, bottom: 40, left: 50 };
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;
    
    // Create SVG
    const svg = d3
      .select(svgNode)
      .attr('width', width)
      .attr('height', height)
      .append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);
    
    // Set up scales
    const xScale = d3
      .scaleLinear()
      .domain([0, 200]) // Hockey rink length is 200ft
      .range([0, innerWidth]);
    
    const yScale = d3
      .scaleLinear()
      .domain([0, 85]) // Hockey rink width is 85ft
      .range([innerHeight, 0]);
    
    // Define max value for color scale
    const actualMaxValue = maxValue || d3.max(data, d => d.value) || 1;
    
    // Set up color scale
    const colorScale = d3
      .scaleLinear<string>()
      .domain([0, actualMaxValue])
      .range(colorRange as [string, string]);
    
    // Draw rink outline
    svg
      .append('rect')
      .attr('x', 0)
      .attr('y', 0)
      .attr('width', innerWidth)
      .attr('height', innerHeight)
      .attr('stroke', theme.palette.grey[300])
      .attr('stroke-width', 2)
      .attr('fill', 'none');
    
    // Draw center line
    svg
      .append('line')
      .attr('x1', innerWidth / 2)
      .attr('y1', 0)
      .attr('x2', innerWidth / 2)
      .attr('y2', innerHeight)
      .attr('stroke', theme.palette.grey[300])
      .attr('stroke-width', 2)
      .attr('stroke-dasharray', '5,5');
    
    // Draw blue lines
    svg
      .append('line')
      .attr('x1', xScale(75))
      .attr('y1', 0)
      .attr('x2', xScale(75))
      .attr('y2', innerHeight)
      .attr('stroke', theme.palette.primary.light)
      .attr('stroke-width', 2);
    
    svg
      .append('line')
      .attr('x1', xScale(125))
      .attr('y1', 0)
      .attr('x2', xScale(125))
      .attr('y2', innerHeight)
      .attr('stroke', theme.palette.primary.light)
      .attr('stroke-width', 2);
    
    // Draw heat points - properly typed with HeatmapPoint[]
    const heatPoints = svg
      .selectAll('.heat-point')
      .data<HeatmapPoint>(data)
      .enter()
      .append('circle')
      .attr('class', 'heat-point')
      .attr('cx', d => xScale(d.x))
      .attr('cy', d => yScale(d.y))
      .attr('r', d => Math.max(3, Math.sqrt(d.value) * 10)) // Ensure a minimum radius
      .attr('fill', d => colorScale(d.value))
      .attr('opacity', 0.7)
      .attr('stroke', d => d3.color(colorScale(d.value))?.darker().toString() || '')
      .attr('stroke-width', 1)
      .style('cursor', 'pointer');
    
    // Add event handlers
    heatPoints
      .on('click', function(event, d: HeatmapPoint) {
        if (onPointClick) {
          event.stopPropagation();
          onPointClick(d);
        }
      })
      .on('mouseover', function(event, d: HeatmapPoint) {
        d3.select(this)
          .attr('opacity', 1)
          .attr('stroke-width', 2)
          .attr('r', Math.max(5, Math.sqrt(d.value) * 12)); // Increase size on hover
          
        // Add tooltip (simplified version)
        svg.append('text')
          .attr('class', 'tooltip')
          .attr('x', xScale(d.x) + 10)
          .attr('y', yScale(d.y) - 10)
          .attr('fill', theme.palette.text.primary)
          .text(`Value: ${d.value.toFixed(2)}`);
      })
      .on('mouseout', function(event, d: HeatmapPoint) {
        d3.select(this)
          .attr('opacity', 0.7)
          .attr('stroke-width', 1)
          .attr('r', Math.max(3, Math.sqrt(d.value) * 10)); // Reset size
          
        // Remove tooltip
        svg.selectAll('.tooltip').remove();
      });
    
    // Add X axis
    const xAxis = d3
      .axisBottom(xScale)
      .ticks(10)
      .tickFormat(d => `${d}ft`);
    
    svg
      .append('g')
      .attr('transform', `translate(0,${innerHeight})`)
      .call(xAxis);
    
    // Add Y axis
    const yAxis = d3
      .axisLeft(yScale)
      .ticks(5)
      .tickFormat(d => `${d}ft`);
    
    svg
      .append('g')
      .call(yAxis);
    
    // Add labels if needed
    if (showLabels) {
      // X axis label
      svg
        .append('text')
        .attr('x', innerWidth / 2)
        .attr('y', innerHeight + margin.bottom - 5)
        .attr('text-anchor', 'middle')
        .style('font-size', '12px')
        .style('fill', theme.palette.text.secondary)
        .text('Length (ft)');
      
      // Y axis label
      svg
        .append('text')
        .attr('transform', 'rotate(-90)')
        .attr('x', -innerHeight / 2)
        .attr('y', -margin.left + 15)
        .attr('text-anchor', 'middle')
        .style('font-size', '12px')
        .style('fill', theme.palette.text.secondary)
        .text('Width (ft)');
      
      // Goal label
      svg
        .append('text')
        .attr('x', xScale(100))
        .attr('y', yScale(42.5) - 5)
        .attr('text-anchor', 'middle')
        .style('font-size', '12px')
        .style('fill', theme.palette.text.secondary)
        .text('Goal');
      
      // Goal visual
      svg
        .append('rect')
        .attr('x', xScale(90))
        .attr('y', yScale(45))
        .attr('width', xScale(110) - xScale(90))
        .attr('height', yScale(40) - yScale(45))
        .attr('stroke', theme.palette.error.main)
        .attr('stroke-width', 2)
        .attr('fill', 'none');
    }
    
    // Create a legend
    const legendWidth = 200;
    const legendHeight = 20;
    
    const legendScale = d3
      .scaleLinear()
      .domain([0, actualMaxValue])
      .range([0, legendWidth]);
    
    const legendAxis = d3
      .axisBottom(legendScale)
      .ticks(5)
      .tickFormat(d => `${d.valueOf().toFixed(2)}`);
    
    const legend = svg
      .append('g')
      .attr('transform', `translate(${innerWidth - legendWidth - 20}, ${margin.top})`);
    
    // Create gradient for legend
    const defs = svg.append('defs');
    
    const gradient = defs
      .append('linearGradient')
      .attr('id', `legend-gradient-${Math.random().toString(36).substr(2, 9)}`) // Unique ID to avoid conflicts
      .attr('x1', '0%')
      .attr('y1', '0%')
      .attr('x2', '100%')
      .attr('y2', '0%');
    
    gradient
      .append('stop')
      .attr('offset', '0%')
      .attr('stop-color', colorRange[0]);
    
    gradient
      .append('stop')
      .attr('offset', '100%')
      .attr('stop-color', colorRange[1]);
    
    // Draw legend rectangle
    legend
      .append('rect')
      .attr('width', legendWidth)
      .attr('height', legendHeight)
      .style('fill', `url(#${gradient.attr('id')})`);
    
    // Add legend axis
    legend
      .append('g')
      .attr('transform', `translate(0, ${legendHeight})`)
      .call(legendAxis);
    
    // Add legend title
    legend
      .append('text')
      .attr('x', 0)
      .attr('y', -5)
      .style('font-size', '12px')
      .style('fill', theme.palette.text.secondary)
      .text('Shot Density');
    
    // Return cleanup function to remove all D3 elements when component unmounts
    return () => {
      if (svgNode) {
        d3.select(svgNode).selectAll('*').remove();
      }
    };
  }, [data, width, height, showLabels, colorScheme, maxValue, colorRange, theme, handlePointClick]);
  
  // Handle empty data case
  if (!data || data.length === 0) {
    return (
      <StyledPaper>
        {title && (
          <Typography variant="h6" gutterBottom>
            {title}
          </Typography>
        )}
        <Box display="flex" justifyContent="center" alignItems="center" height={height}>
          <Typography color="textSecondary">No shot data available</Typography>
        </Box>
      </StyledPaper>
    );
  }
  
  return (
    <StyledPaper>
      {title && (
        <Typography variant="h6" gutterBottom>
          {title}
        </Typography>
      )}
      <Box display="flex" justifyContent="center">
        <svg ref={svgRef}></svg>
      </Box>
    </StyledPaper>
  );
};

export default ShotHeatmap;