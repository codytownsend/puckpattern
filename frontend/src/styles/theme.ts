import { createTheme } from '@mui/material/styles';

// Colors from the brand guidelines
const colors = {
  // Primary Colors
  primaryDark: '#2E2E38',
  primaryLight: '#97DFFC',
  background: '#F9F5EF',
  
  // Supporting Colors
  secondaryAccent: '#FF5A5F',
  successGreen: '#3ECF8E',
  warningAmber: '#FFB84D',
  errorRed: '#E63946',
  
  // Text Colors
  darkText: '#1A1A24',
  mediumText: '#4F4F5C',
  lightText: '#8C8C99',
  
  // Grayscale
  gray100: '#F7F7F9',
  gray200: '#E9E9ED',
  gray300: '#D1D1D8',
  gray400: '#ABABBB',
  gray500: '#8C8C99',
  gray600: '#6B6B78',
  gray700: '#4F4F5C',
};

// Create a theme instance
const theme = createTheme({
  palette: {
    primary: {
      main: colors.primaryLight,
      dark: colors.primaryDark,
      contrastText: colors.darkText,
    },
    secondary: {
      main: colors.secondaryAccent,
      contrastText: '#ffffff',
    },
    background: {
      default: colors.background,
      paper: colors.gray100,
    },
    error: {
      main: colors.errorRed,
    },
    warning: {
      main: colors.warningAmber,
    },
    success: {
      main: colors.successGreen,
    },
    text: {
      primary: colors.darkText,
      secondary: colors.mediumText,
      disabled: colors.lightText,
    },
    grey: {
      100: colors.gray100,
      200: colors.gray200,
      300: colors.gray300,
      400: colors.gray400,
      500: colors.gray500,
      600: colors.gray600,
      700: colors.gray700,
    },
  },
  typography: {
    fontFamily: [
      'Inter',
      '-apple-system',
      'BlinkMacSystemFont',
      '"Segoe UI"',
      'Roboto',
      '"Helvetica Neue"',
      'Arial',
      'sans-serif',
    ].join(','),
    h1: {
      fontWeight: 700,
      fontSize: '2.5rem',
      lineHeight: 1.2,
      color: colors.darkText,
    },
    h2: {
      fontWeight: 600,
      fontSize: '2rem',
      lineHeight: 1.3,
      color: colors.darkText,
    },
    h3: {
      fontWeight: 600,
      fontSize: '1.75rem',
      lineHeight: 1.4,
      color: colors.darkText,
    },
    h4: {
      fontWeight: 600,
      fontSize: '1.5rem',
      lineHeight: 1.4,
      color: colors.darkText,
    },
    h5: {
      fontWeight: 600,
      fontSize: '1.25rem',
      lineHeight: 1.4,
      color: colors.darkText,
    },
    h6: {
      fontWeight: 600,
      fontSize: '1rem',
      lineHeight: 1.5,
      color: colors.darkText,
    },
    body1: {
      fontSize: '1rem',
      lineHeight: 1.5,
      color: colors.darkText,
    },
    body2: {
      fontSize: '0.875rem',
      lineHeight: 1.5,
      color: colors.mediumText,
    },
    subtitle1: {
      fontSize: '1rem',
      lineHeight: 1.5,
      fontWeight: 500,
      color: colors.mediumText,
    },
    subtitle2: {
      fontSize: '0.875rem',
      lineHeight: 1.5,
      fontWeight: 500,
      color: colors.mediumText,
    },
    button: {
      textTransform: 'none',
      fontWeight: 600,
    },
  },
  shape: {
    borderRadius: 8,
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          padding: '8px 16px',
          boxShadow: 'none',
          '&:hover': {
            boxShadow: 'none',
          },
        },
        contained: {
          '&:hover': {
            boxShadow: 'none',
          },
        },
        containedPrimary: {
          backgroundColor: colors.primaryLight,
          color: colors.darkText,
          '&:hover': {
            backgroundColor: '#7ABFE3', // Slightly darker primary light
          },
        },
        containedSecondary: {
          backgroundColor: colors.secondaryAccent,
          '&:hover': {
            backgroundColor: '#E6515B', // Slightly darker secondary
          },
        },
        outlined: {
          borderWidth: 2,
          '&:hover': {
            borderWidth: 2,
          },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          boxShadow: '0px 4px 20px rgba(0, 0, 0, 0.05)',
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundColor: colors.primaryDark,
        },
      },
    },
    MuiTableHead: {
      styleOverrides: {
        root: {
          backgroundColor: colors.gray200,
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        head: {
          fontWeight: 600,
          color: colors.darkText,
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          fontWeight: 500,
        },
      },
    },
    MuiLink: {
      styleOverrides: {
        root: {
          color: colors.primaryLight,
          '&:hover': {
            color: '#7ABFE3', // Slightly darker primary light
          },
        },
      },
    },
  },
});

export { colors };
export default theme;