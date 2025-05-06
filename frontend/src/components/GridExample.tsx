import { Grid } from '@mui/material';

// In Material UI v5, we need to use Grid as follows:
// Instead of <Grid item>, we use <Grid item={true}>

const GridExampleCorrect = () => (
  <Grid container spacing={3}>
    <Grid item={true} xs={12} md={6}>
      {/* Content goes here */}
    </Grid>
    <Grid item={true} xs={12} md={6}>
      {/* More content */}
    </Grid>
  </Grid>
);

export default GridExampleCorrect;